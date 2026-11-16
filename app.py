    if players <= 5:
        return "Mittel"
    return "Voll"


def occupancy_color(label):
    return {
        "Leer": "#17803d",
        "Wenig": "#70a943",
        "Mittel": "#d18b00",
        "Voll": "#c83d3d",
    }.get(label, "#667085")


# Modell beim Start laden.
try:
    model = load_model()
    model_error = None
except Exception as exc:
    model = None
    model_error = str(exc)


# Kopfbereich
st.markdown(
    """
    <div style="display:flex;align-items:center;gap:12px">
      <span style="font-size:2.4rem">⚽</span>
      <div>
        <h1 style="margin:0">Bolzplatzradar</h1>
        <span style="color:#667085">
          Finde den passenden Bolzplatz – voll für Mitspieler oder frei für Platz.
        </span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")

if model is None:
    st.warning(
        "Das KI-Modell ist gerade nicht verfügbar. "
        "Prüfe, ob keras_model.h5 im Projekt-Hauptverzeichnis liegt."
    )
    with st.expander("Technische Information"):
        st.code(model_error or "Unbekannter Fehler")


# Suche und Filter
with st.sidebar:
    st.subheader("📍 Platz suchen")
    search = st.text_input("Ort oder Platzname", placeholder="z. B. Kreuzberg")

    st.subheader("Filter")
    fullness_filter = st.selectbox(
        "Auslastung",
        ["Alle", "Leer", "Wenig", "Mittel", "Voll"],
    )

    surfaces = ["Alle"] + sorted({place["surface"] for place in PLACES})
    surface_filter = st.selectbox("Untergrund", surfaces)


# Foto-Upload und Vorhersage
with st.expander("📷 Foto eines Bolzplatzes hochladen"):
    st.caption(
        "Das Foto wird mit dem im Projekt hinterlegten Modell ausgewertet. "
        "Es wird durch diesen Demo-Code nicht dauerhaft gespeichert."
    )

    uploaded_photo = st.file_uploader(
        "Platzfoto auswählen",
        type=["jpg", "jpeg", "png"],
        key="place_photo",
    )

    if uploaded_photo is not None:
        try:
            photo = Image.open(uploaded_photo).convert("RGB")
            st.image(
                photo,
                caption="Ausgewähltes Platzfoto",
                use_container_width=True,
            )

            if model is not None:
                if st.button("Auslastung schätzen"):
                    labels = load_labels()

                    try:
                        prediction_label, confidence = predict_occupancy(
                            photo,
                            model,
                            labels,
                        )
                        st.success(
                            f"Geschätzte Auslastung: **{prediction_label}** "
                            f"(Modell-Konfidenz: {confidence:.0%})"
                        )
                    except Exception as exc:
                        st.error(f"Die Vorhersage ist fehlgeschlagen: {exc}")
            else:
                st.info(
                    "Die Schätzung ist nicht verfügbar, solange das Modell fehlt."
                )

        except Exception as exc:
            st.error(f"Das Foto konnte nicht geöffnet werden: {exc}")


# Platzliste
st.subheader("Bolzplätze in deiner Nähe")

sort_option = st.selectbox(
    "Sortieren nach",
    [
        "Empfohlen",
        "Am wenigsten besucht",
        "Am meisten besucht",
        "Entfernung",
    ],
)

filtered_places = []

for place in PLACES:
    level = occupancy_from_demo_players(place["players"])

    if fullness_filter != "Alle" and level != fullness_filter:
        continue

    if surface_filter != "Alle" and place["surface"] != surface_filter:
        continue

    query = search.strip().lower()
    if (
        query
        and query not in place["name"].lower()
        and query not in place["area"].lower()
    ):
        continue

    filtered_places.append(place)


if sort_option == "Am wenigsten besucht":
    filtered_places.sort(key=lambda place: place["players"])
elif sort_option == "Am meisten besucht":
    filtered_places.sort(key=lambda place: place["players"], reverse=True)
elif sort_option == "Entfernung":
    filtered_places.sort(key=lambda place: place["distance"])


if not filtered_places:
    st.info("Keine Plätze gefunden. Ändere deine Suche oder Filter.")
else:
    for index, place in enumerate(filtered_places):
        level = occupancy_from_demo_players(place["players"])
        color = occupancy_color(level)

        with st.container(border=True):
            image_col, info_col = st.columns([1, 2])

            with image_col:
                st.image(place["image"], use_container_width=True)

            with info_col:
                st.markdown(f"### {place['name']}")
                st.caption(
                    f"📍 {place['area']} · {place['distance']} km entfernt"
                    f" · {place['surface']} · {place['facilities']}"
                )

                st.markdown(
                    f"<span style='background:{color};color:white;"
                    f"padding:5px 10px;border-radius:14px;font-weight:600'>"
                    f"{level} · {place['players']} Spieler</span>",
                    unsafe_allow_html=True,
                )

                st.write(f"**{place['note']}**")
                st.caption(
                    f"Zuletzt aktualisiert {place['updated']} · Demodaten"
                )
                st.progress(
                    min(place["players"] / 10, 1.0),
                    text="Beispiel-Auslastung",
                )
                st.button("Details", key=f"details_{index}")
