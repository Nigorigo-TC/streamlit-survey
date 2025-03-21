import streamlit as st
import pandas as pd
import os
import sys
import subprocess

# **Streamlit アプリのタイトル**
st.title("コンディション記録アンケート")

# **データ保存用のCSVファイル**
csv_file = "condition_survey.csv"

# **基本情報**
st.subheader("基本情報")
name = st.text_input("名前を入力してください")
date = st.date_input("日付を選択してください")

# **1. 全般的な体調**
st.subheader("1. 全般的な体調")
health_condition = st.slider("とても悪い ー とても良い", 0, 100, 50)

# **2. 疲労感**
st.subheader("2. 疲労感")
fatigue = st.slider("とても強い ー 全く無い", 0, 100, 50)

# **3. 睡眠時間**
st.subheader("3. 睡眠時間")
sleep_hours = st.number_input("睡眠時間（時間）", min_value=0, max_value=12, step=1, value=6)
sleep_minutes = st.number_input("睡眠時間（分）", min_value=0, max_value=59, step=1, value=30)

# **4. 睡眠の深さ**
st.subheader("4. 睡眠の深さ")
sleep_quality = st.slider("とても浅い ー とても深い", 0, 100, 50)

# **5. 睡眠の状況（複数選択）**
st.subheader("5. 睡眠の状況")
sleep_issues = st.multiselect(
    "該当するものを選んでください",
    ["夢を見た", "何回も目覚めた", "何回もトイレに行った", "寝汗をかいた", "寝付けなかった", "特になし"]
)

# **6. 食欲**
st.subheader("6. 食欲")
appetite = st.slider("全く無い ー とてもある", 0, 100, 50)

# **7. 故障の有無**
st.subheader("7. 故障の有無")
injury = st.radio("故障はありますか？", ["無", "有"])
injury_part = ""
if injury == "有":
    injury_part = st.text_input("故障の部位を入力してください")

# **9. 練習強度（昨日）**
st.subheader("9. 練習強度（昨日）")
training_intensity = st.slider("非常にきつい ー 非常に楽", 0, 100, 50)

# **10. 排便（昨日）**
st.subheader("10. 排便（昨日）")
bowel_movement = st.radio("排便の有無", ["有", "無"])
bowel_times = 0
if bowel_movement == "有":
    bowel_times = st.number_input("排便回数", min_value=1, max_value=10, step=1)

# **11. 便の形**
st.subheader("11. 便の形")
st.text("※裏面の便イラストを参考に記入")
st.text_input("便の形を入力してください")

# **12. 走行距離**
st.subheader("12. 走行距離")
running_distance = st.number_input("走行距離（km）", min_value=0.0, max_value=100.0, step=0.1)

# **13. 運動時間・きつさ**
st.subheader("13. 運動時間・きつさ")
exercise_time = st.number_input("運動時間（分）", min_value=0, max_value=300, step=5)
exercise_difficulty = st.slider("運動のきつさ", 0, 100, 50)

# **特記事項**
st.subheader("特記事項")
symptoms = st.multiselect(
    "該当するものを選んでください",
    ["頭痛", "のどの痛み", "鼻水", "咳", "痰", "息苦しさ", "強いだるさ", "臭いがわかりにくい", "味がわかりにくい", "吐き気", "嘔吐", "その他"]
)
other_symptoms = ""
if "その他" in symptoms:
    other_symptoms = st.text_input("その他の症状を記入してください")

# **データ保存**
if st.button("送信"):
    data = {
        "名前": name,
        "日付": str(date),
        "全般的な体調": health_condition,
        "疲労感": fatigue,
        "睡眠時間": f"{sleep_hours}時間 {sleep_minutes}分",
        "睡眠の深さ": sleep_quality,
        "睡眠の状況": ", ".join(sleep_issues),
        "食欲": appetite,
        "故障": injury,
        "故障部位": injury_part,
        "練習強度": training_intensity,
        "排便": bowel_movement,
        "排便回数": bowel_times,
        "便の形": "",
        "走行距離": running_distance,
        "運動時間": exercise_time,
        "運動きつさ": exercise_difficulty,
        "症状": ", ".join(symptoms),
        "その他症状": other_symptoms
    }

    df = pd.DataFrame([data])

    try:
        # **ファイルが存在しない場合、ヘッダー付きで作成**
        if not os.path.exists(csv_file):
            df.to_csv(csv_file, mode="w", index=False, encoding="utf-8")
        else:
            df.to_csv(csv_file, mode="a", header=False, index=False, encoding="utf-8")

        st.success("回答ありがとうございました！")
    except Exception as e:
        st.error(f"データの保存に失敗しました: {e}")

# **過去のデータを表示**
if st.checkbox("過去の回答を見る"):
    if os.path.exists(csv_file):
        try:
            df = pd.read_csv(csv_file)
            st.write(df)
        except Exception as e:
            st.error(f"データの読み込みに失敗しました: {e}")
    else:
        st.warning("まだデータがありません。")

# **ポート設定を追加**
if __name__ == "__main__":
    script_path = os.path.abspath(sys.argv[0])  # 現在のスクリプトのフルパスを取得
    subprocess.run(["streamlit", "run", script_path, "--server.port", "8503"], shell=True)