import streamlit as st
import pandas as pd
import json
from io import BytesIO

st.set_page_config(page_title="Quiz Master", layout="centered")
st.title("📋 Quiz Master (Streamlit Edition)")

# Initialize session state
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = pd.DataFrame()
    st.session_state.filtered_data = pd.DataFrame()
    st.session_state.scores = {}
    st.session_state.used_questions = set()
    st.session_state.current_index = 0
    st.session_state.teams = [f"Team {chr(65+i)}" for i in range(15)]
    for team in st.session_state.teams:
        st.session_state.scores[team] = {}

# Load File
uploaded_file = st.file_uploader("Upload your Excel quiz file", type="xlsx")
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.session_state.quiz_data = df.copy()
    st.session_state.filtered_data = df.copy()
    st.session_state.used_questions = set()
    st.session_state.current_index = 0
    st.success("Quiz file loaded successfully!")

# Filter Section
if not st.session_state.quiz_data.empty:
    with st.expander("🔍 Filters"):
        rounds = st.session_state.quiz_data['Round'].dropna().unique()
        types = st.session_state.quiz_data['Type'].dropna().unique()
        subtypes = st.session_state.quiz_data['Sub Type'].dropna().unique()

        selected_round = st.selectbox("Round", [""] + list(rounds))
        selected_type = st.selectbox("Type", [""] + list(types))
        selected_subtype = st.selectbox("Sub Type", [""] + list(subtypes))

        if st.button("Apply Filters"):
            filtered = st.session_state.quiz_data.copy()
            if selected_round:
                filtered = filtered[filtered['Round'] == selected_round]
            if selected_type:
                filtered = filtered[filtered['Type'] == selected_type]
            if selected_subtype:
                filtered = filtered[filtered['Sub Type'] == selected_subtype]
            filtered = filtered[~filtered.index.isin(st.session_state.used_questions)]
            st.session_state.filtered_data = filtered
            st.session_state.current_index = 0
            st.success(f"{len(filtered)} question(s) available.")

# Show Current Question
if not st.session_state.filtered_data.empty:
    filtered = st.session_state.filtered_data
    idx = st.session_state.current_index

    if idx < len(filtered):
        row = filtered.iloc[idx]
        st.subheader(f"Q{idx + 1}: {row['Question']}")
        if st.button("💡 Show Answer"):
            st.info(row['Answer'])

        team = st.selectbox("Select Team", st.session_state.teams, key="team_select")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ Award 10", key="award"):
                round_name = row['Round']
                st.session_state.scores[team][round_name] = st.session_state.scores[team].get(round_name, 0) + 10
                st.session_state.used_questions.add(row.name)
                st.session_state.filtered_data = filtered[~filtered.index.isin(st.session_state.used_questions)]
                st.session_state.current_index = 0
        with col2:
            if st.button("❌ Deduct 10", key="deduct"):
                round_name = row['Round']
                st.session_state.scores[team][round_name] = st.session_state.scores[team].get(round_name, 0) - 10
                st.session_state.used_questions.add(row.name)
                st.session_state.filtered_data = filtered[~filtered.index.isin(st.session_state.used_questions)]
                st.session_state.current_index = 0
        with col3:
            if st.button("➡️ Next Question", key="next"):
                st.session_state.current_index += 1
    else:
        st.info("No more questions available.")

# Score Display
if st.session_state.scores:
    st.markdown("---")
    st.subheader("📊 Scores")
    score_text = ""
    top_scores = []
    for team, rounds in st.session_state.scores.items():
        total = sum(rounds.values())
        round_scores = ", ".join([f"{r}: {s}" for r, s in rounds.items()])
        score_text += f"**{team}** - {round_scores} | **Total**: {total}\n"
        top_scores.append((team, total))
    st.markdown(score_text)

    # Show Top 3
    st.subheader("🏆 Top 3 Teams")
    top_scores = sorted(top_scores, key=lambda x: x[1], reverse=True)[:3]
    for i, (team, score) in enumerate(top_scores, 1):
        st.markdown(f"{i}. **{team}** - {score} points")

# Export Score
if st.button("📥 Export Scores"):
    rows = []
    all_rounds = sorted({r for team_scores in st.session_state.scores.values() for r in team_scores})
    for team, round_scores in st.session_state.scores.items():
        row = {"Team": team, **{r: round_scores.get(r, 0) for r in all_rounds}}
        row['Total'] = sum(round_scores.values())
        rows.append(row)
    df_scores = pd.DataFrame(rows)

    output = BytesIO()
    df_scores.to_excel(output, index=False)
    st.download_button("Download Excel", data=output.getvalue(), file_name="quiz_scores.xlsx")
