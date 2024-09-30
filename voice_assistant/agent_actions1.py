import requests
import json
import time
from datetime import datetime

access_token = None
token_expiry = None

def get_access_token():
    global access_token, token_expiry

    if access_token and token_expiry and time.time() < token_expiry:
        return access_token

    url = "https://www.hodlmd.com/BotApi/GenerateToken"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "appID": "71333698-F12B-43A9-AFD7-EA1EBE9241AE",
        "appKey": "8D0EDCDD-703F-4061-88FF-BD7F57202117",
        "userID": 8,
        "userType": "D",
        "appType": "A"
    }

    response = requests.post(url, headers=headers, json=data, verify=False)#verify = False because getting Expired SSL certificate error keep it true for production
    result = response.json()

    if result.get("errorCode") == "0":
        access_token = result["token"]
        token_expiry = time.time() + 3600
        return access_token
    else:
        raise Exception(f"Failed to retrieve token: {result.get('message')}")

def add_appointment(visit_datetime, doctor_id = 8, consultation_type = 15, call_type = 0, user_id = 623):
    token = get_access_token()

    url = "https://www.hodlmd.com/BotApi/AddAppointment"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
        "data": {
            "doctorConsultationTypeID": consultation_type,
            "docotrID": doctor_id,
            "visitDateTime": visit_datetime,
            "callType": call_type,
            "userID": user_id
        },
        "action": "add",
        "intent": "add_appointment",
        "module": "calendar"
    }

    response = requests.post(url, headers=headers, json=data, verify=False)#verify = False because getting Expired SSL certificate error keep it true for production
    return response.json()

def get_availability(doctor_id = 8, call_type = 0):
    token = get_access_token()

    url = "https://www.hodlmd.com/BotApi/GetAvailability"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
        "data": {
            "doctorID": doctor_id,
            "callType": call_type
        },
        "action": "getdata",
        "intent": "get_availability",
        "module": "calendar"
    }

    response = requests.post(url, headers=headers, json=data, verify=False)#verify = False because getting Expired SSL certificate error keep it true for production
    return response.json()

def get_availability_as_per_time(date, time="00:00:00", doctor_id = 8, call_type = 0):
    token = get_access_token()

    url = "https://www.hodlmd.com/BotApi/GetAvailabilityAsPerTime"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
        "data": {
            "doctorID": doctor_id,
            "date": date,
            "time": time,
            "callType": call_type
        },
        "action": "getdata",
        "intent": "get_availability",
        "module": "calendar"
    }

    response = requests.post(url, headers=headers, json=data, verify=False)#verify = False because getting Expired SSL certificate error keep it true for production
    
    return response.json()

def process_availability(date):
    try:
        user_date = datetime.strptime(date, "%Y-%m-%d").date()
        current_date = datetime.now().date()
        if user_date < current_date:
            return {"error": "The date cannot be in the past. Please provide a valid future date."}
        
        response = get_availability_as_per_time(date)
        
        if response["errorCode"] == "0":
            slots = response.get("Slot", [])
            
            if slots:
                current_time = datetime.now().time() if user_date == current_date else None
                picked_slots = [
                    slot for i, slot in enumerate(slots)
                    if slot.get("isBooked", "") != "Y"
                    and (current_time is None or datetime.strptime(slot["time"], "%I:%M %p").time() > current_time)
                ]

                return {
                    "message": "Slots retrieved successfully.",
                    "picked_slots": picked_slots
                }
            else:
                return {
                    "message": "No available slots.",
                    "picked_slots": []
                }
        else:
            if response["message"] == "String was not recognized as a valid DateTime.":
                return {"error": "Invalid date format. Please provide the date in a valid format (e.g., YYYY-MM-DD)."}
            elif response["message"] == "Slot not available.":
                return {"error": f"No slots available for the selected date: {date}."}
            else:
                return {"error": f"An unknown error occurred: {response['message']}"}
    
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}
    
def convert_to_12_hour_format(time_24):
    hours, minutes = map(int, time_24.split(':'))

    if hours >= 12:
        period = 'PM'
        if hours > 12:
            hours -= 12
    else:
        period = 'AM'
        if hours == 0:
            hours = 12

    return f"{hours}:{minutes:02d} {period}"
    
def get_available_slots(date, start_time, end_time):
    date_slots = process_availability(date)
    # start_time = convert_to_12_hour_format(start_time)
    # end_time = convert_to_12_hour_format(end_time)
    start_time_dt = datetime.strptime(start_time, '%I:%M %p')
    end_time_dt = datetime.strptime(end_time, '%I:%M %p')

    picked_slots = date_slots.get("picked_slots", [])

    filtered_slots = []
    for slot in picked_slots:
        slot_time_dt = datetime.strptime(slot['time'], '%I:%M %p')
        
        if start_time_dt <= slot_time_dt <= end_time_dt:
            filtered_slots.append(slot['time'])

    if len(filtered_slots) == 0:
        return "No slots for this time" 

    return ', '.join(filtered_slots)

def get_doctor_time(date):
    date_slots = get_availability_as_per_time(date)
    picked_slots = date_slots.get("Slot", [])
    start_time = picked_slots[0]['time']
    end_time = picked_slots[-1]['time']
    doctor_time = f"{start_time} to {end_time}"
    return doctor_time


def is_slot_available(visit_datetime):
    date_str = visit_datetime.strftime("%Y-%m-%d")
    
    availability_response = process_availability(date_str)

    if "error" in availability_response:
        return False

    picked_slots = availability_response.get("picked_slots", [])

    for slot in picked_slots:
        if slot.get("isBooked", "") != "Y":
            slot_time = datetime.strptime(slot['time'], "%I:%M %p").time()
            visit_time = visit_datetime.time()

            if slot_time == visit_time:
                return True

    return False

def schedule_appointment(user_input):
    try:
        visit_datetime = datetime.strptime(user_input, "%Y-%m-%d %I:%M:%S %p")

        if visit_datetime < datetime.now():
            return {"error": "The date and time cannot be in the past. Please provide a valid future datetime."}

        if not is_slot_available(visit_datetime):
            return {"error": "Doctor not available for the requested time."}

        appointment_response = add_appointment(visit_datetime.strftime("%Y-%m-%d %I:%M:%S %p"))

        if appointment_response.get("errorCode") == "1":
            return appointment_response.get("message")
        else:
            return "Appointment booked successfully."

    except ValueError as e:
        return  f"ExceptionMessage:{str(e)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

# user_input = "2024-10-06"
# dates = get_availaible_slots(user_input, "02:00 PM", "02:30 PM")
# print(dates)
# user_input = "2024-10-06 03:00:00 PM"
# result = schedule_appointment(user_input)
# print(result)
# user_input = "2024-10-06"
# dates = get_available_slots(user_input, "16:00", "18:00")
# print(dates)
# user_input = "2024-10-06"
# result = get_doctor_time(user_input)
# print(result)