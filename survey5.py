import streamlit as st
import requests
from datetime import date
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Supabase 接続情報 ---
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_key"]
TABLE_NAME = "condition"

# --- Supabaseにデータ送信 ---
def submit_to_supabase(data_dict):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    data_dict["exported"] = False  # 新規は未出力とする
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}",
        json=data_dict,  # リストではなく辞書を直接送信
        headers=headers
    )
    if response.status_code != 201:
        st.error(f"❌ Supabaseへの送信に失敗しました: {response.status_code} {response.text}")
        return False
    return True

# --- Supabaseから未出力データ取得 ---
def fetch_unexported_data():
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?exported=eq.false&select=*"
    res = requests.get(url, headers=headers)
    return pd.DataFrame(res.json())

# --- Supabaseのデータをexported=trueに更新 ---
def mark_as_exported(ids):
    if not ids:
        return
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    for record_id in ids:
        url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?id=eq.{record_id}"
        requests.patch(url, headers=headers, json={"exported": True})

# --- Googleスプレッドシート出力 ---
SPREADSHEET_NAME = "2025年度_起床時コンディションチェック（実業団・NF）"
SHEET_NAME = "condition2025"

def export_to_gsheet(df):
    df = df.fillna("")
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["google_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

    existing_data = sheet.get_all_values()
    if not existing_data:
        sheet.insert_row(df.columns.tolist(), 1)  # ヘッダーがない場合のみ追加

    sheet.append_rows(df.values.tolist())

# --- スライダー（数値非表示）関数 ---
def secret_slider_with_labels(title, left_label, right_label, key, min_value=0, max_value=100, default=50):
    st.markdown(f"**{title}**")
    value = st.select_slider(
        label=" ",
        options=list(range(min_value, max_value + 1)),
        value=default,
        format_func=lambda x: "",
        key=key,
        label_visibility="collapsed"
    )
    st.markdown(f"<div style='display: flex; justify-content: space-between;'><span>{left_label}</span><span>{right_label}</span></div>", unsafe_allow_html=True)
    return value
    
# --- ping監視対応（UptimeRobotなど） ---
query_params = st.query_params
if query_params.get("ping", ["0"])[0] == "1":
    st.write("pong")  # 応答確認用
    st.stop()         # それ以上の処理を止める
    
# --- 送信完了フラグ初期化 ---
if "submitted" not in st.session_state:
    st.session_state["submitted"] = False

# --- 管理者判定 ---
query_params = st.query_params
is_admin = query_params.get("admin", ["0"])[0] == "1"

# ========================
# 管理者ページ（?admin=1）
# ========================
if is_admin:
    st.title("🛠 管理者メニュー（未出力データ → スプレッドシート）")
    admin_pass = st.text_input("管理者パスワードを入力", type="password", key="admin_password_input")

    if admin_pass == st.secrets.get("admin_password"):
        if st.button("📤 未出力データを出力する"):
            df = fetch_unexported_data()
            if df.empty:
                st.warning("⚠ 未出力データはありません")
            else:
                export_to_gsheet(df.drop(columns=["exported"]))
                mark_as_exported(df["id"].tolist())
                st.success(f"✅ {len(df)} 件のデータを出力し、exported=true に更新しました！")
    elif admin_pass:
        st.error("❌ パスワードが間違っています")
        
# ========================
# 一般ユーザー用ページ
# ========================
if not is_admin:
    st.title("Record of the physical condition")

    if not st.session_state["submitted"]:
        date_val = st.date_input("**1. Date**", value=date.today(), key="date")
        st.caption(" ")

        st.markdown("**2. Team name**")
        team = st.text_input("hidden", key="team", label_visibility="collapsed")
        st.caption(" ")

        st.markdown("**3. Name**")
        name = st.text_input("hidden", key="name", label_visibility="collapsed")
        st.caption("※ Please enter your full name")

        health_condition = secret_slider_with_labels("4. Body condition", "Very Bad", "Very Good", "health")
        st.caption(" ")

        fatigue = secret_slider_with_labels("5. Fatigue", "Very Bad", "Very Good", "fatigue")
        st.caption(" ")

        st.markdown("**6. Amount of sleep（ex. 7h15min→7.25、7h30min→7.5）**")
        sleep_time = st.number_input("hidden", 0.0, 24.0, step=0.1, key="sleep_time", label_visibility="collapsed")
        st.caption("※You can also enter it manually")

        sleep_quality = secret_slider_with_labels("7. Deepness of sleep", "Very Shallow", "Very Deep", "sleep_quality")
        st.caption(" ")

        st.markdown("**8. Sleep quality（multile choice）**")
        sleep_issues = st.multiselect("hidden", [
            "Had a dream", "Woke up many times", "Went to restroom many times", "Perspired in sleep", "Uneasy to sleep", "None"], key="sleep_issues", label_visibility="collapsed")
        st.caption(" ")

        appetite = secret_slider_with_labels("9. Appetite", "Very Small", "Very Big", "appetite")
        st.caption(" ")

        injury = st.radio("**10. Injury**", ["without", "with"], key="injury")
        st.caption(" ")

        st.markdown("**11. Injured area**")
        injury_part = st.text_input("hidden", key="injury_part", label_visibility="collapsed") if injury == "with" else ""
        st.caption("※ If you are injured, please describe the specific location of the injury（ex. right ankle）")

        injury_severity = secret_slider_with_labels("12. Severity of injury", "Worst pain", "No Pain", "injury_severity")
        st.caption(" ")

        training_intensity = secret_slider_with_labels("13. Training intensity（yesterday）", "Very Hard", "Very Easy", "training_intensity")
        st.caption(" ")

        bowel_movement = st.radio("**14. Defecation**", ["Yes", "No"], key="bowel_movement")
        st.caption(" ")

        st.image("stool_chart.png", caption="Type of stool（1～7）", use_container_width=True)

        st.markdown("**15. Type of stool（yesterday）**")
        bowel_shape = st.selectbox("Please select the corresponding number with reference to the image above", list(range(1, 8)), key="bowel_shape") if bowel_movement == "有" else ""
        st.caption("※ Please select based on the image")

        running_distance = st.number_input("**16. Running distance（yesterday）**", 0.0, 100.0, step=0.1, key="running_distance")
        st.caption("※You can also enter it manually")

        spo2 = st.number_input("**17. SpO2**", 70, 100, key="spo2")
        st.caption("※You can also enter it manually")

        pulse = st.number_input("**18. Pulse rate**", 20, 200, key="pulse")
        st.caption("※You can also enter it manually")

        temperature = st.number_input("**19. Body temerature**", 33.0, 42.0, step=0.1, key="temperature")
        st.caption("※You can also enter it manually")

        weight = st.number_input("**20. Body weight**", 20.0, 150.0, step=0.1, key="weight")
        st.caption("※You can also enter it manually")

        symptoms = st.multiselect("**21. Special notes（multiple choice）**", [
            "None", "Cough", "Runny nose", "Headache", "Shortness of breath", "Diarrhea", "Sore throat", "Chills",
            "Abdominal pain", "Feeling feverish", "Severe fatigue（extreme tiredness）", "Nausea", "Phlegm", "Menstruation", "Irregular bleeding", "Taking medication", "Other（please specify）"], key="symptoms")
        st.caption("※If none apply, please select 'None'")

        other_symptoms = st.text_input("21-1. Other symptoms", key="other_symptoms") if "Other（please specify）" in symptoms else ""
        if "Other（please specify）" in symptoms:
            st.caption(" ")

        options = [None] + list(range(0, 301))
        exercise_time = st.selectbox("**22. Yesterday's training time（min） ※You can also enter it manually**",
                                     options=options,
                                     format_func=lambda x: "Please enter" if x is None else f"{x} min",
                                     key="exercise_time")
        st.caption("※Warm-up and cool-down time don't need to be included")


        st.image("rpe_chart.png", caption="Training intensity（0～10）", use_container_width=True)
        rpe_options = [None] + list(range(0,11))
        exercise_rpe = st.selectbox("**23. Yesterday's training intensity（RPE）**", 
                                    options = rpe_options,
                                    format_func=lambda x: "Please enter" if x is None else str(x),
                                    key="exercise_rpe")
        st.caption("※Please enter the training intensity（RPE）based on the image above")

        if st.button("Submit"):
            if not team or not name:
                st.error("❗ Please enter your team and name")
            elif injury == "有" and not injury_part:
                st.error("❗ Please enter your '11. injured area'")
            elif not symptoms:
                st.error("❗ Please select your '21. Special notes（multiple choice）'")
            elif "その他" in symptoms and not other_symptoms:
                st.error("❗ Please enter your '21-1. other symptoms'")
            elif exercise_time is None:
                st.error("❗ Please enter your '22. Yesterday's training time（min）'")
            elif exercise_rpe is None:
                st.error("❗ Please enter your '23. Yesterday's training intensity'")
            else:
                data = {
                    "date": str(date_val), "team": team, "name": name,
                    "health": health_condition, "fatigue": fatigue,
                    "sleep_time": sleep_time, "sleep_quality": sleep_quality,
                    "sleep_issues": ", ".join(sleep_issues), "appetite": appetite,
                    "injury": injury, "injury_part": injury_part,
                    "injury_severity": injury_severity, "training_intensity": training_intensity,
                    "bowel_movement": bowel_movement, "bowel_shape": bowel_shape,
                    "running_distance": running_distance, "spo2": spo2, "pulse": pulse,
                    "temperature": temperature, "weight": weight,
                    "symptoms": ", ".join(symptoms), "other_symptoms": other_symptoms,
                    "exercise_time": exercise_time, "exercise_rpe": exercise_rpe
                }
                if submit_to_supabase(data):
                    st.session_state["submitted"] = True
                    st.rerun()
                else:
                    st.error("❌ Supabaseへの送信に失敗しました。")
    else:
        st.success("✅ Thank you for your response！")
        st.balloons()
        st.markdown("Thank you, and have a great day！")

