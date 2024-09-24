import datetime
import csv
import json
from groq import Groq
from voice_assistant.config import Config

MODEL = 'llama3-groq-70b-8192-tool-use-preview'

# Doctor availability data
doctors_data = [
{
    "name": "Dr. Ali",
    "specialty": "Cardiologist",
    "available_slots": [
        "2024-09-25 09:00",
        "2024-09-25 10:00"
    ]
},
{
    "name": "Dr. Bilal",
    "specialty": "Dentist",
    "available_slots": [
        "2024-09-26 11:00",
        "2024-09-26 12:00"
    ]
},
{
    "name": "Dr. Mehar",
    "specialty": "Dermatologist",
    "available_slots": [
        "2024-09-27 14:00",
        "2024-09-27 15:00"
    ]
},
{
    "name": "Dr. Rana",
    "specialty": "Neurologist",
    "available_slots": [
        "2024-09-27 14:00",
        "2024-09-27 15:00"
    ]
}
]

# Storage for scheduled meetings
scheduled_meetings = []
meeting_file = 'doctor_meetings.csv'

# Show available doctors
def show_available_doctors():
    """
    Returns the list of available doctors and their specialties in JSON format.
    """
    return json.dumps(doctors_data, indent=4)

# Check if a doctor is available at the requested time
def check_doctor_availability(doctor_name, requested_time):
    """
    Check if the doctor is available at the requested time.
    """
    for doctor in doctors_data:
        if doctor['name'] == doctor_name:
            if requested_time in doctor['available_slots']:
                return True
            else:
                return False
    return False

# Schedule a meeting with the doctor
def schedule_meeting(doctor_name, patient_name, requested_time):
    """
    Schedule a meeting with a doctor, check their availability, and update the CSV file.
    """
    for doctor in doctors_data:
        if doctor['name'] == doctor_name:
            if requested_time in doctor['available_slots']:
                # Remove the time slot from the doctor's available slots
                doctor['available_slots'].remove(requested_time)

                # Record the meeting
                meeting = {
                    "doctor": doctor_name,
                    "patient": patient_name,
                    "time": requested_time
                }
                scheduled_meetings.append(meeting)

                # Save the updated schedule to CSV
                save_meetings_to_csv()

                return json.dumps({"status": "success", "message": f"Meeting scheduled with {doctor_name} at {requested_time}"})
            else:
                return json.dumps({"status": "error", "message": f"{doctor_name} is not available at {requested_time}"})
    return json.dumps({"status": "error", "message": "Doctor not found"})

# Save scheduled meetings to CSV
def save_meetings_to_csv():
    """
    Save the scheduled meetings to a CSV file.
    """
    with open(meeting_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Doctor", "Patient", "Time"])
        for meeting in scheduled_meetings:
            writer.writerow([meeting['doctor'], meeting['patient'], meeting['time']])

# Load scheduled meetings from CSV
def load_meetings_from_csv():
    """
    Load the existing scheduled meetings from the CSV file.
    """
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
        pass  # No meetings file exists yet

# Handle the conversation and doctor scheduling requests
def run_conversation(messages, client):
    """
    Simulate a conversation and handle scheduling-related actions.
    """
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
                "name": "schedule_meeting",
                "description": "Schedule a meeting with a doctor",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "doctor_name": {"type": "string", "description": "Name of the doctor"},
                        "patient_name": {"type": "string", "description": "Name of the patient"},
                        "requested_time": {"type": "string", "description": "Requested meeting time (YYYY-MM-DD HH:MM)"}
                    },
                    "required": ["doctor_name", "patient_name", "requested_time"],
                },
            },
        },
    ]

    # Map available functions
    available_functions = {
        "show_available_doctors": show_available_doctors,
        "schedule_meeting": schedule_meeting,
    }

    # Handle tool calls based on the conversation
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
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(**function_args)
            
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": function_response,
            })

        second_response = client.chat.completions.create(
            model=MODEL,
            messages=messages
        )
        return second_response.choices[0].message.content

    return response_message.content

# Initialize and load any existing scheduled meetings
load_meetings_from_csv()