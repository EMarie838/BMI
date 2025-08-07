
#imports flask date/time etc..
from flask import Flask, render_template, request, jsonify
from transformers import pipeline #import for machine learning model 
import datetime
import os 
import csv
#creates application
app = Flask(__name__)

chatbot = pipeline("text-generation", model="microsoft/DialoGPT-small") #initialsing chabot pipeline 

#filenames for storing data 
DATA_FILE = "bmi_data.csv"
WATER_FILE = "water_data.csv"
SLEEP_FILE = "sleep_data.csv"
STEPS_COUNTER_FILE = "steps_counter.csv"

@app.route("/", methods=['GET', 'POST'])
def home():
    result = None 
    latest = get_latest_bmi_entry()
    labels = ["Day 1", "Day 2", "Day 3"]
    chart_data = [22, 23.5, 24.1]
    water_today = get_today_water_total()
    sleep_today = get_today_sleep_total()

    if request.method == 'POST':
        height = float(request.form['height'])
        weight = float(request.form['weight'])
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        bmi, status = calculate_bmi(height, weight)
        save_bmi_to_csv(date, height, weight, bmi, status)
        result = {"bmi": round(bmi, 2), "status": status}

    return render_template(
        "index.html",
        result=result,
        latest=latest,
        labels=labels,
        chart_data=chart_data,
        water_today=water_today,
        sleep_today=sleep_today
    )

@app.route("/chatbot", methods=["POST"]) #etsablishes connection between URL and chatbot to perform a specific task and will only respond to HTTP POST requests 
def chatbot_route(): #function thats called when user posts to chabot
    user_message = request.form["message"] #variables takes in user message (value) from the field named "message" from the POST request
    ai_response = str(chatbot(user_message)[0]['generated_text']) #first the value has to be a string, second sends user message to AI model (chatbot = pipeline) mdoel returns response object, [0]['generated_text'] to take the actual resposne
    
#adding the custom health advice
    if "water" in user_message.lower():
         ai_response += "\nTip: Aim for at least 8 cups (2liters) of water per day." 
    elif "steps" in user_message.lower():
         ai_response += "\nTip: Try to walk 10 000 steps daily." 
    elif "sleep" in user_message.lower():
         ai_response += "\nTip: Aim for 7-9 hours of sleep each night." 
    elif "gain weight" in user_message.lower():
         ai_response += "\nMeal Advice: Add healthy snacks, increase calorie intake and focus on increasing protein levels."
    elif "lose weight" in user_message.lower():
         ai_response += "\nMeal Advice: Have meals that are high in protein, low in carbs and fats to decrease calorie intake. Focus on vegetables, lean protein, and whole grains." 
    return jsonify({"response": ai_response}) 


def save_bmi_to_csv(date, height, weight, bmi, status):
    file_exists = os.path.isfile(DATA_FILE)
    with open(DATA_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Date', 'Height (cm)', 'Weight (kg)', 'BMI', 'Status'])
        writer.writerow([date, height, weight, round (bmi, 2),  status])

def calculate_bmi(height_cm, weight_kg):
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    if bmi < 18.5:
        status = "Underweight"
    elif 18.5 <= bmi < 25:
        status = "Normal weight"
    elif 25 <= bmi < 30:
        status = "Overweight"
    else:
        status = "Obesity"
    return bmi, status

def get_latest_bmi_entry():
    if not os.path.exists(DATA_FILE):
        return None

    with open(DATA_FILE, newline='') as file:
        reader = csv.DictReader(file)
        latest_entry = None
        for row in reader:
            if latest_entry is None or row['Date'] > latest_entry['Date']:
                latest_entry = row
        return latest_entry

def save_water_entry(date, amount):
    file_exists = os.path.isfile(WATER_FILE)
    with open(WATER_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Date", "Amount (mL)"])
        writer.writerow([date, amount])

def get_today_water_total():
    today = datetime.datetime.now().date()
    if not os.path.exists(WATER_FILE):
        return 0

    total = 0
    with open(WATER_FILE, newline='') as file:
        reader = csv.reader(file)
        next(reader)  # skip header
        for row in reader:
            row_date = datetime.datetime.strptime(row[0], "%Y-%m-%d").date()
            if row_date == today:
                total += int(row[1])
    return total

def save_sleep_entry(date, hours):
    file_exists = os.path.isfile(SLEEP_FILE)
    with open(SLEEP_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Date", "Hours Slept"])
            writer.writerow([date, hours]) 

def get_today_sleep_total():
                today = datetime.datetime.now().date()
                if not os.path.exists(SLEEP_FILE):
                    return 0
                
                total = 0 
                with open(SLEEP_FILE, newline='') as file:
                    reader = csv.reader(file)
                    next(reader)
                    for row in reader:
                        row_date = datetime.datetime.strptime(row[0], "%Y-%m-%d").date()
                        if row_date == today:
                            total += float(row[1])
                return total
            
def save_steps_counter_entry(date, steps):
        file_exists = os.path.isfile(STEPS_COUNTER_FILE)
        with open(STEPS_COUNTER_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["Date", "Steps"])
                writer.writerow([date, steps])

def get_today_steps_counter_total():
                    today = datetime.datetime.now().date()
                    if not os.path.exists(STEPS_COUNTER_FILE):
                        return 0 
                    
                    total = 0 
                    with open(STEPS_COUNTER_FILE, newline= '') as file:
                        reader = csv.reader(file)
                        next(reader)
                        for row in reader:
                            row_date = datetime.datetime.strptime(row[0], "%Y-%m-%d").date()
                            if row_date == today:
                                total += float(row[1])
                        return total

#takes in water intake logging form submission 
#saves data and updates total and puts it into the dashboard             

@app.route("/water", methods=["POST"])
def log_water():
    amount = int(request.form["water"])
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    save_water_entry(today, amount)
    water_today = get_today_water_total()
    # Get other dashboard data
    result = None
    latest = get_latest_bmi_entry()
    labels = ["Day 1", "Day 2", "Day 3"]
    chart_data = [22, 23.5, 24.1]
    sleep_today = get_today_sleep_total()
    steps_today = get_today_steps_counter_total()
    return render_template(
        "index.html",
        result=result,
        latest=latest,
        labels=labels,
        chart_data=chart_data,
        water_today=water_today,
        sleep_today=sleep_today,
        steps_today=steps_today
    )

#takes in sleep logging form submission 
#saves data and updates total and puts it into the dashboard

@app.route("/sleep", methods=["POST"])
def log_sleep_counter():
    hours = float(request.form["sleep_hours"])
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    save_sleep_entry(today, hours)
    sleep_today = get_today_sleep_total()
    # Get other dashboard data
    result = None
    latest = get_latest_bmi_entry()
    labels = ["Day 1", "Day 2", "Day 3"]
    chart_data = [22, 23.5, 24.1]
    water_today = get_today_water_total()
    steps_today = get_today_steps_counter_total()
    return render_template(
        "index.html",
        result=result,
        latest=latest,
        labels=labels,
        chart_data=chart_data,
        water_today=water_today,
        sleep_today=sleep_today,
        steps_today=steps_today
    )
     
     #takes in steps logging form submission 
     #saves data and updates total and puts it into the dashboard
@app.route("/steps_counter", methods=["POST"])
def log_steps_counter():
    steps = int(request.form["steps_counter"])
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    save_steps_counter_entry(today, steps)
    steps_today = get_today_steps_counter_total()
    # Get other data for dashboard
    result = None
    latest = get_latest_bmi_entry()
    labels = ["Day 1", "Day 2", "Day 3"]
    chart_data = [22, 23.5, 24.1]
    water_today = get_today_water_total()
    sleep_today = get_today_sleep_total()
    return render_template(
        "index.html",
        result=result,
        latest=latest,
        labels=labels,
        chart_data=chart_data,
        water_today=water_today,
        sleep_today=sleep_today,
        steps_today=steps_today
    )

if __name__ == '__main__':
    app.run(debug=True, port=5050)
# starts Flask development server when script is run 