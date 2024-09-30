import datetime
import csv
import json
from groq import Groq
from voice_assistant.config import Config
from .agent_actions1 import schedule_appointment, get_available_slots

MODEL = 'llama3-groq-70b-8192-tool-use-preview'

doctors_data = [
    {
        "name": "Dr. Ali",
        "specialty": "Cardiologist",
    },
    {
        "name": "Dr. Bilal",
        "specialty": "Dentist",
    },
    {
        "name": "Dr. Mehar",
        "specialty": "Dermatologist",
    },
    {
        "name": "Dr. Rana",
        "specialty": "Neurologist",
    }
]

scheduled_meetings = []
meeting_file = 'doctor_meetings.csv'

def is_valid_interval(requested_time, available_time):
    requested_dt = datetime.datetime.strptime(requested_time, "%Y-%m-%d %I:%M %p")
    available_dt = datetime.datetime.strptime(available_time, "%Y-%m-%d %I:%M %p")
    interval = abs((requested_dt - available_dt).total_seconds() / 60)
    return interval % 5 == 0

def show_available_doctors():
    return json.dumps(doctors_data, indent=4)

def check_doctor_availability(doctor_name, requested_time):
    for doctor in doctors_data:
        if doctor['name'] == doctor_name:
            for slot in doctor['available_slots']:
                if slot == requested_time and is_valid_interval(slot, requested_time):
                    return True
            return False
    return False

def suggest_other_slots(doctor_name):
    for doctor in doctors_data:
        if doctor['name'] == doctor_name:
            return doctor['available_slots']
    return []

def schedule_meeting(doctor_name, patient_name, requested_time=None, auto_schedule=False):
    for doctor in doctors_data:
        if doctor['name'] == doctor_name:
            if requested_time and requested_time in doctor['available_slots'] and is_valid_interval(requested_time, requested_time):
                doctor['available_slots'].remove(requested_time)
                meeting = {"doctor": doctor_name, "patient": patient_name, "time": requested_time}
                scheduled_meetings.append(meeting)
                save_meetings_to_csv()
                return json.dumps({"status": "success", "message": f"Meeting scheduled with {doctor_name} at {requested_time}"})
            
            elif auto_schedule:
                for available_time in doctor['available_slots']:
                    if is_valid_interval(available_time, available_time):
                        doctor['available_slots'].remove(available_time)
                        meeting = {"doctor": doctor_name, "patient": patient_name, "time": available_time}
                        scheduled_meetings.append(meeting)
                        save_meetings_to_csv()
                        return json.dumps({"status": "success", "message": f"Meeting auto-scheduled with {doctor_name} at {available_time}"})
                return json.dumps({"status": "error", "message": f"No valid slots for {doctor_name}."})

            else:
                available_slots = suggest_other_slots(doctor_name)
                valid_slots = [slot for slot in available_slots if is_valid_interval(slot, slot)]
                if valid_slots:
                    return json.dumps({"status": "error", "message": f"{doctor_name} is not available at {requested_time}. Available slots: {', '.join(valid_slots)}"})
                else:
                    return json.dumps({"status": "error", "message": f"No available slots for {doctor_name}."})
    
    return json.dumps({"status": "error", "message": "Doctor not found"})

def save_meetings_to_csv():
    with open(meeting_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Doctor", "Patient", "Time"])
        for meeting in scheduled_meetings:
            writer.writerow([meeting['doctor'], meeting['patient'], meeting['time']])

def load_meetings_from_csv():
    try:
        with open(meeting_file, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                scheduled_meetings.append({
                    "doctor": row['Doctor'],
                    "patient": row['Patient'],
                    "time": row['Time']
                })
    except FileNotFoundError:
        pass  

def run_conversation(messages, client):
    tools = [
        {
            "type": "function",
            "function": {
                "name": "show_available_doctors",
                "description": "Show all available doctors",
                "parameters": {}
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_available_slots",
                "description": "Retrieve available time slots for appointments within a specified date and time range",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "The date for which available slots are requested (format: YYYY-MM-DD).",
                            "required": True
                        },
                        "start_time": {
                            "type": "string",
                            "description": "The start time for filtering available slots (format: HH:MM AM/PM).",
                            "required": True
                        },
                        "end_time": {
                            "type": "string",
                            "description": "The end time for filtering available slots (format: HH:MM AM/PM).",
                            "required": True
                        }
                    },
                    "required": ["date", "start_time", "end_time"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "schedule_appointment",
                "description": "Schedule an appointment with a doctor at a specific time",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_input": {"type": "string", "description": "Datetime for appointment (YYYY-MM-DD HH:MM:SS AM/PM)", "required": True}
                    }
                },
            },
        },
    ]

    available_functions = {
        "show_available_doctors": show_available_doctors,
        "get_available_slots": get_available_slots,
        "schedule_appointment": schedule_appointment
    }

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        max_tokens=4096
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls 

    if tool_calls:
        messages.append(response_message)

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions.get(function_name)  # Use .get() to safely access the function
            
            if function_to_call:
                function_args = json.loads(tool_call.function.arguments)
                print(function_args)
                if function_name == "get_available_slots":
                    print("we were here")
                    # Convert 24-hour time to 12-hour format
                    if 'start_time' in function_args:
                        hour, minute = map(int, function_args['start_time'].split(':'))
                        am_pm = "AM" if hour < 12 else "PM"
                        hour = hour % 12 or 12  # Convert 0 to 12 for 12 AM
                        function_args['start_time'] = f"{hour}:{minute:02d} {am_pm}"

                    if 'end_time' in function_args:
                        hour, minute = map(int, function_args['end_time'].split(':'))
                        am_pm = "AM" if hour < 12 else "PM"
                        hour = hour % 12 or 12  # Convert 0 to 12 for 12 AM
                        function_args['end_time'] = f"{hour}:{minute:02d} {am_pm}"
                
                if function_name == "schedule_appointment":
                    print("we were here")
                    # Convert 24-hour time to 12-hour format
                    if 'user_input' in function_args:
                        time_obj = datetime.datetime.strptime(function_args['user_input'], "%Y-%m-%d %H:%M:%S")
                        formatted_time = time_obj.strftime("%I:%M:%S %p")
                        date_str = function_args['user_input'].split()[0]
                        final_string = f"{date_str} {formatted_time}"
                        function_args['user_input'] = final_string

                print(f"Executing function: {function_name} with arguments: {function_args}")
                function_response = function_to_call(**function_args)
                print(f"Function {function_name} executed successfully, response: {function_response}")

                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                })

                if function_name == "show_doctors_slots":
                    picked_slots = function_response.get("picked_slots", [])
                    picked_times = [slot['time'] for slot in picked_slots if 'time' in slot]
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": "picked_times",
                        "content": f"{picked_times}",
                    })

        second_response = client.chat.completions.create(
            model=MODEL,
            messages=messages
        )
        return second_response.choices[0].message.content

    return response_message.content