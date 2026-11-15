import streamlit as st
import pandas as pd
from google import genai

# 1. Pobranie klucza i inicjalizacja nowego klienta API
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error(f"Błąd konfiguracji klienta API: {e}")
    client = None

st.set_page_config(page_title="Flame in Freefall | SI Dashboard", page_icon="🔥", layout="wide")

st.sidebar.title("Navigation")
page = st.sidebar.radio("Select Module:", ["🏠 Home", "📊 PSI Experiment Database", "💡 SI Assistant", "🌪️ CFD Analysis"])

if page == "🏠 Home":
    st.title("🔥 Flame in Freefall: Spacecraft Fire Safety Dashboard")
    st.markdown("""
    **Project Goal:** To provide a Super Intelligence (SI) powered interface to analyze microgravity combustion data from the NASA Physical Science Informatics (PSI) database.
    """)

elif page == "📊 PSI Experiment Database":
    st.title("Data Explorer: Normal vs Inverse Flames")
    
    # 1. Zaktualizowane menu z odwrotnymi płomieniami (Inverse Flames)
    dataset_choice = st.selectbox("Select experimental dataset:", [
        "psi_10.csv (Ethylene - C2H4 | Normal Flame)", 
        "psi_159.csv (Ethane - C2H6 | Normal Flame)",
        "psi_10_inverse.csv (Ethylene - C2H4 | Inverse Flame)",
        "psi_159_inverse.csv (Ethane - C2H6 | Inverse Flame)"
    ])
    
    # 2. Wyciągamy samą nazwę pliku z wybranej opcji
    file_to_load = dataset_choice.split(" ")[0]
    
    try:
        # Wczytujemy plik
        df = pd.read_csv(file_to_load, sep=",")
        
        # MAGICZNA LINIJKA: Usuwa złośliwe, ukryte spacje z nazw wszystkich kolumn
        df.columns = df.columns.str.strip()
        
        # 3. Dynamiczna informacja dla Jury NASA wyświetlana w zależności od pliku
        if "inverse" in file_to_load:
            st.info("💡 **Inverse Diffusion Flame (IDF) Data:** In this experiment, the oxidizer (oxygen) is injected into a fuel-rich environment. NASA studies IDF in microgravity to cleanly isolate soot formation and carbon particulate emissions without the interference of buoyancy-induced flickering.")
        else:
            st.info("💡 **Normal Diffusion Flame Data:** Standard combustion setup where fuel is injected into an oxygen-rich environment.")
        
        if 'Fuel' in df.columns:
            selected_fuel = st.selectbox("Select fuel type:", ["All"] + list(df['Fuel'].dropna().unique()))
            if selected_fuel != "All":
                df = df[df['Fuel'] == selected_fuel]
        st.dataframe(df, use_container_width=True)
        
        # --- DYNAMICZNE ROZPOZNAWANIE KOLUMN (Etylen vs Etan) ---
        p_col = 'pmean (atm)' if 'pmean (atm)' in df.columns else 'approx p (bar)' if 'approx p (bar)' in df.columns else None
        o2_col = 'XO2 (init)' if 'XO2 (init)' in df.columns else 'XO2 before test' if 'XO2 before test' in df.columns else 'XO2' if 'XO2' in df.columns else None

        st.subheader("Thermodynamics: Temperature vs. Pressure")
        if p_col and 'Tad (K)' in df.columns:
            df_plot = df.copy()
            df_plot[p_col] = pd.to_numeric(df_plot[p_col], errors='coerce')
            df_plot['Tad (K)'] = pd.to_numeric(df_plot['Tad (K)'], errors='coerce')
            df_plot = df_plot.dropna(subset=[p_col, 'Tad (K)'])
            st.scatter_chart(data=df_plot, x=p_col, y='Tad (K)')
        else:
            st.warning("⚠️ Brak kolumn ciśnienia lub temperatury do wygenerowania wykresu.")

        st.subheader("Combustion Dynamics: Oxygen Concentration vs. Temperature")
        if o2_col and 'Tad (K)' in df.columns:
            df_ox = df.copy()
            df_ox[o2_col] = pd.to_numeric(df_ox[o2_col], errors='coerce')
            df_ox['Tad (K)'] = pd.to_numeric(df_ox['Tad (K)'], errors='coerce')
            df_ox = df_ox.dropna(subset=[o2_col, 'Tad (K)'])
            st.scatter_chart(data=df_ox, x=o2_col, y='Tad (K)')
        else:
            st.info("⚠️ Brak kolumn stężenia tlenu do wygenerowania wykresu.")

        st.subheader("Combustion Dynamics: Oxygen Concentration vs. Pressure")
        if o2_col and p_col:
            df_stab = df.copy()
            df_stab[o2_col] = pd.to_numeric(df_stab[o2_col], errors='coerce')
            df_stab[p_col] = pd.to_numeric(df_stab[p_col], errors='coerce')
            df_stab = df_stab.dropna(subset=[o2_col, p_col])
            st.scatter_chart(data=df_stab, x=o2_col, y=p_col)
        else:
            st.info("⚠️ Brak kolumn stężenia tlenu do wygenerowania wykresu.")
            
    except Exception as e:
        st.error(f"Data loading error: Upewnij się, że plik '{file_to_load}' znajduje się w folderze projektu! Szczegóły: {e}")

elif page == "💡 SI Assistant":
    st.title("Spacecraft Fire Safety AI Assistant")
    st.write("Ask a question regarding flame behavior, material flammability, or the PSI-10 data. The AI will analyze the loaded knowledge base and raw experimental data.")
    
    user_query = st.text_area("Enter your question (e.g., 'How does a 30% oxygen concentration affect flames?'):")
    
    if st.button("Search & Analyze"):
        if not client:
            st.error("⚠️ API Client not initialized.")
        elif not user_query:
            st.warning("Please enter a question first.")
        else:
            with st.spinner("Analyzing NASA knowledge base and dataset..."):
                try:
                    # Wczytanie plików
                    try:
                        with open("NASA_Combustion_Knowledge.txt", "r", encoding="utf-8") as f:
                            knowledge_text = f.read()
                    except:
                        knowledge_text = "Knowledge base file not found."

                    try:
                        df_ai = pd.read_csv("psi_10.csv", sep=",")
                        data_text = df_ai.to_csv(index=False) 
                    except:
                        data_text = "Data table not available."

                    prompt = f"""
                    You are an expert AI aerospace engineer built for the NASA Space Apps challenge.
                    Your goal is to answer the user's question based ONLY on the following knowledge base and experimental data.
                    If the answer is in the data, extract it. If not, say you don't know based on current data.
                    
                    --- KNOWLEDGE BASE ---
                    {knowledge_text}
                    
                    --- PSI EXPERIMENTAL DATA (CSV FORMAT) ---
                    {data_text}
                    
                    --- USER QUESTION ---
                    {user_query}
                    """
                    
                    # Nowa metoda generowania odpowiedzi (API v2)
                    response = client.models.generate_content(
                        model='gemini-3.1-flash-lite',
                        contents=prompt
                    )
                    
                    st.success("Analysis Complete:")
                    st.write(response.text)
                    
                except Exception as e:
                    st.error(f"AI Generation Error: {e}")

elif page == "🌪️ CFD Analysis":
    st.title("CFD Simulations: Gravity Effects on Combustion")
    st.markdown("""
    Comparison of 2D axisymmetric combustion simulations performed in **Ansys Fluent**. 
    The results demonstrate the critical role of buoyancy in flame shape, species transport, and temperature distribution across different gravitational environments.
    """)
    
    # Pierwszy rząd (Ziemia i Mars)
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🌍 Earth (1g)")
        try:
            st.image("fluent_1g.png", caption="Temperature Contour (-9.81 m/s²)", use_container_width=True)
        except:
            st.warning("⚠️ Brakuje pliku 'fluent_1g.png' w folderze.")
            
    with col2:
        st.subheader("🔴 Mars (0.38g)")
        try:
            st.image("fluent_mars.png", caption="Temperature Contour (-3.72 m/s²)", use_container_width=True)
        except:
            st.warning("⚠️ Brakuje pliku 'fluent_mars.png' w folderze.")
            
    st.markdown("---") # Linia oddzielająca rzędy
    
    # Drugi rząd (Księżyc i Mikrograwitacja)
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("🌕 Moon (0.16g)")
        try:
            st.image("fluent_moon.png", caption="Temperature Contour (-1.62 m/s²)", use_container_width=True)
        except:
            st.warning("⚠️ Brakuje pliku 'fluent_moon.png' w folderze.")
            
    with col4:
        st.subheader("🌌 Microgravity (0g)")
        try:
            st.image("fluent_0g.png", caption="Temperature Contour (0 m/s²)", use_container_width=True)
        except:
            st.warning("⚠️ Brakuje pliku 'fluent_0g.png' w folderze.")