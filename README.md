# 📘 Timetable Management System

A **Flask-based web application** for managing school or college timetables with features for uploading CSV files, viewing schedules, detecting clashes, and generating calendar events.

---

## ✨ Features

* 📥 **CSV Upload** – Upload teacher lists and timetable data via CSV
* 📊 **Timetable View** – Filter and edit timetable entries
* 📆 **Calendar View** – FullCalendar integration for interactive weekly view
* ⚠️ **Clash Detection** – Automatically detect scheduling conflicts
* 🔁 **RRULE Generation** – Export recurring events for calendar apps
* 👨‍🏫 **Teacher Management** – Color-coded assignments per teacher
* 📱 **Responsive UI** – Works on desktop and mobile devices

---

## 🧱 Prerequisites

* Python 3.7 or higher
* `pip` (Python package installer)

---

## ⚙️ Installation

```bash
# Clone the repository
git clone <your-repository-url>
cd timetable-management-system

# Create a virtual environment (recommended)
python -m venv timetable_env

# Activate the environment
# On Windows:
timetable_env\Scripts\activate
# On macOS/Linux:
source timetable_env/bin/activate

# Install required packages
pip install flask pandas werkzeug python-dateutil
```

# Install all required packages
pip install -r requirements.txt

> **Note:** The `uploads` directory is auto-created on first run if missing.

---

## 🗂️ Project Structure

```
timetable-management-system/
├── app.py                 # Main Flask app
├── uploads/              # Uploaded CSVs
├── templates/            # HTML templates
│   ├── index.html
│   ├── upload.html
│   ├── timetable.html
│   ├── calendar.html
│   └── edit_timetable.html
├── static/               # CSS & JS
└── README.md
```

---

## 🚀 Usage

### 1. Starting the Application

```bash
python app.py
```

Access the app at:
➡️ **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 📂 2. CSV File Format

### Teachers CSV (`teachers.csv`)

```csv
Teacher Name,Subject,Department
John Doe,Mathematics,Science
Jane Smith,English,Humanities
```

### Timetable CSV (`timetable.csv`)

```csv
Teacher Name,Subject,Day,Period,Time Slot,Class/Activity
John Doe,Mathematics1,Monday,1,09:00 to 10:00,Class A
Jane Smith,English2,Tuesday,2,10:00 to 11:00,Class B
```

> **Formatting Notes:**
>
> * Time must be `"HH:MM to HH:MM"`
> * Day must be fully spelled out (`Monday`, `Tuesday`, etc.)
> * Subject names can include numbers and will be cleaned automatically

---

## 🧭 3. Step-by-Step Guide for Users

### ✅ A. Running the Application

1. Clone the repository and set up the virtual environment (see above).
2. Run the application:

   ```bash
   python app.py
   ```
3. Open your browser and go to:
   **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

### 📤 B. Uploading Files

1. Go to the **Upload Page**: [http://127.0.0.1:5000/upload](http://127.0.0.1:5000/upload)
2. **Step 1**: Upload the **Timetable CSV** (`timetable.csv`)
3. **Step 2**: Upload the **Teachers List CSV** (`teachers.csv`)

   > ⚠️ Upload these files **one after the other**, not simultaneously.

---

### 📅 C. Navigating to Views

* **Timetable View**:
  👉 [http://127.0.0.1:5000/timetable](http://127.0.0.1:5000/timetable)

* **Calendar View**:
  👉 [http://127.0.0.1:5000/calendar](http://127.0.0.1:5000/calendar)

---

### 🛠️ D. Resolving Conflicts in Timetable View

In the **Timetable View**:

* Conflicts appear if a **teacher is assigned multiple sessions** at the same time.
* Look for duplicate teacher names in the same time slot.
* Use the **Edit** button next to a conflicting entry to modify or reassign it.

---

### 📆 E. Viewing Timetables in Calendar View

In the **Calendar View**:

* Use filters to display events by:

  * **Teacher**
  * **Subject**
  * **Class/Activity**
* Weekly recurring events are displayed automatically.
* If **duplicates appear**, it may be due to:

  * Re-uploading CSVs with overlapping data
  * Incorrect formatting
* To resolve duplicates:

  * Clean the source CSVs and re-upload
  * Use the conflict resolution tools in Timetable View

---

### 🔗 F. Direct URLs

| Page           | URL                                                                |
| -------------- | ------------------------------------------------------------------ |
| Home           | [http://127.0.0.1:5000](http://127.0.0.1:5000)                     |
| Upload         | [http://127.0.0.1:5000/upload](http://127.0.0.1:5000/upload)       |
| Timetable View | [http://127.0.0.1:5000/timetable](http://127.0.0.1:5000/timetable) |
| Calendar View  | [http://127.0.0.1:5000/calendar](http://127.0.0.1:5000/calendar)   |

---

## 🧪 API Endpoints

| Endpoint          | Description                             |
| ----------------- | --------------------------------------- |
| `/api/events`     | Get calendar events (filters supported) |
| `/api/clashes`    | Get scheduling conflicts                |
| `/generate_rrule` | Generate RRULE strings for export       |

### API Parameters for `/api/events`:

* `teacher` – Filter by teacher name
* `subject` – Filter by subject
* `class` – Filter by class/activity
* `start` – Start date (ISO format)
* `end` – End date (ISO format)

---
