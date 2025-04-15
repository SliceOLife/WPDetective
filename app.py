import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

headers = {"User-Agent": "Mozilla/5.0"}

def get_businesses(query, location, max_pages=1):
    businesses = []
    base_url = "https://www.telefoonboek.nl/zoeken"
    formatted_query = query.replace(" ", "-")
    formatted_location = location.replace(" ", "-")
    search_path = f"{formatted_query}/{formatted_location}"

    for page in range(1, max_pages + 1):
        st.info(f"📄 Pagina {page} ophalen...")
        url = f"{base_url}/{search_path}/pagina{page}/"

        try:
            response = requests.get(url, headers=headers)

            # Save raw HTML for inspection
            with open(f"pagina{page}.html", "w", encoding="utf-8") as f:
                f.write(response.text)

            soup = BeautifulSoup(response.text, 'html.parser')

            # Try with select instead of find_all
            cards = soup.select("a.searchresult")
            st.write(f"[DEBUG] {len(cards)} kaarten gevonden op pagina {page}")

            if len(cards) == 0:
                st.warning(f"[DEBUG] Geen resultaten gevonden op pagina {page}. Check 'pagina{page}.html'")

            for card in cards:
                name = card.get("data-name", "Onbekend").strip()
                meta_url = card.find("meta", itemprop="url")
                website = meta_url["content"].strip() if meta_url else None

                phone_meta = card.find("meta", itemprop="telephone")
                phone = phone_meta["content"].strip() if phone_meta else ""

                description_div = card.find("div", class_="searchresult__review--text")
                description = description_div.text.strip() if description_div else ""

                if website:
                    businesses.append({
                        "Bedrijfsnaam": name,
                        "Website": website,
                        "Telefoonnummer": phone,
                        "Omschrijving": description
                    })

                time.sleep(0.5)

        except Exception as e:
            st.error(f"Fout op pagina {page}: {e}")

    return businesses

def is_wordpress(url):
    try:
        response = requests.get(url, timeout=5, headers=headers)
        if "wp-content" in response.text or "wp-includes" in response.text:
            return True
        soup = BeautifulSoup(response.text, 'html.parser')
        meta = soup.find("meta", attrs={"name": "generator"})
        if meta and "wordpress" in meta.get("content", "").lower():
            return True
        return False
    except:
        return False

# def visualize_results(df):
#     st.subheader("📋 Visuele weergave van resultaten")

#     # Filteroptie op CMS-type
#     cms_filter = st.multiselect(
#         "📌 Filter op CMS-type",
#         options=df["CMS"].unique().tolist(),
#         default=df["CMS"].unique().tolist()
#     )

#     # Filteren
#     filtered_df = df[df["CMS"].isin(cms_filter)]

#     # Geen resultaten?
#     if filtered_df.empty:
#         st.info("Geen bedrijven gevonden met de geselecteerde filters.")
#         return

#     # Toon per bedrijf een ‘kaartje’
#     for _, row in filtered_df.iterrows():
#         st.markdown(f"""
#         ### {row['Bedrijfsnaam']}
#         🌐 [Website]({row['Website']})  
#         📞 **Telefoon:** {row.get('Telefoonnummer', 'Onbekend')}  
#         🧩 **CMS:** {row['CMS']}  
#         📝 *{row.get('Omschrijving', 'Geen omschrijving beschikbaar')}*
#         """)
#         st.divider()

# Streamlit UI
st.set_page_config(page_title="WPDetective", page_icon="🕵️", layout="wide")
st.title("🕵️ WPDetective")
st.subheader("Zoek lokale bedrijven en check of ze WordPress gebruiken")

bedrijfstype = st.selectbox(
    "Bedrijfstype", ["kapper", "bakker", "fysiotherapeut", "slager", "restaurant", "andere..."]
)
if bedrijfstype == "andere...":
    bedrijfstype = st.text_input("Specificeer bedrijfstype", "")

plaats = st.text_input("Plaats", "Dordrecht")
pagina_aantal = st.slider("Aantal pagina’s om te doorzoeken", 1, 5, 2)
alleen_wp = st.checkbox("📌 Toon alleen WordPress-websites")

if st.button("🔎 Start zoeken"):
    if not bedrijfstype or not plaats:
        st.warning("Vul zowel een bedrijfstype als een plaats in.")
    else:
        st.write(f"Zoeken naar **{bedrijfstype}** in **{plaats}** over {pagina_aantal} pagina(s)...")
        results = get_businesses(bedrijfstype, plaats, pagina_aantal)

        for r in results:
            r["CMS"] = "WordPress" if is_wordpress(r["Website"]) else "Niet WordPress"

        df = pd.DataFrame(results)

        if alleen_wp:
            df = df[df["CMS"] == "WordPress"]

        st.success(f"{len(df)} resultaten gevonden.")
        st.dataframe(df, use_container_width=True)
        #visualize_results(df)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download CSV", data=csv, file_name="wpdetective_resultaten.csv", mime="text/csv")