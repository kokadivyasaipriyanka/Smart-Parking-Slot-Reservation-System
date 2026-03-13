# Smart Parking Slot Reservation System

A cloud-based Smart Parking Slot Reservation System built with **HTML/CSS/JavaScript frontend** and **Python Flask backend**.  
The application supports parking slot management, reservation booking, user authentication, admin controls, notifications, and cloud deployment using AWS services.

---

## Features

### User Features
- User registration and login
- Book a parking slot
- View own reservations
- Edit own reservations
- Cancel own reservations

### Admin Features
- Admin login from the same login page
- Manage parking slots
- Manage users
- View all reservations
- Update reservation status

### Cloud Features
- **EC2** for hosting the Flask application
- **RDS PostgreSQL** for database storage
- **S3** for file storage
- **SNS** for email notifications
- **Lambda** for auto-releasing expired reservations

### Custom Library
- **parking-availability-library**
- Published to PyPI and used in the application for:
  - booking conflict detection
  - slot availability calculation
  - slot recommendation
  - occupancy calculation

---

## Project Structure

```text
smart-parking-system/
├── app.py
├── config.py
├── .env
├── requirements.txt
├── README.md
├── models/
├── routes/
├── templates/
├── static/
├── utils/
````

---

## Technologies Used

* Python
* Flask
* PostgreSQL
* HTML
* CSS
* JavaScript
* AWS EC2
* AWS RDS
* AWS S3
* AWS SNS
* AWS Lambda
* boto3

---

## Local Setup Instructions

### 1. Clone or open the project folder

```bash
cd smart-parking-system
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

#### Windows

```bash
.\venv\Scripts\Activate.ps1
```

#### Linux / Mac

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create or update the `.env` file:

```env
SECRET_KEY=your-super-secret-key
DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

DB_HOST=your_aws_host
DB_PORT=5432
DB_NAME=smart_parking_db
DB_USER=postgres
DB_PASSWORD=your_db_password

AWS_REGION=ap-south-1
S3_BUCKET_NAME=your-s3-bucket-name
SNS_TOPIC_ARN=your-sns-topic-arn
MAX_CONTENT_LENGTH=5242880

DEFAULT_ADMIN_NAME=System Admin
DEFAULT_ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_PASSWORD=Admin@123
DEFAULT_ADMIN_PHONE=9999999999
```

### 6. Run the application

```bash
python app.py
```

### 7. Open in browser

```text
http://localhost:5000
```

---

## Default Admin Login

The application automatically creates a default admin account on startup.

* **Email:** `admin@example.com`
* **Password:** `Admin@123`

You can change these values in `.env`.

---

## Database Setup

Create a PostgreSQL database named:

```text
smart-parking-db
```

The application automatically creates the required tables when it starts.

---

## AWS Deployment Overview

### EC2

Used to host the Flask application.

### RDS PostgreSQL

Used to store:

* users
* parking slots
* reservations
* notification logs

### S3

Used for file upload storage.

### SNS

Used to send reservation-related email notifications.

### Lambda

Used to detect expired reservations and release slots automatically.

---

## Custom Library

### Package Name

`parking-availability-library`

### PyPI Link

Add your PyPI project URL here:

```text
https://pypi.org/project/parking-availability-library/0.1.0/
```

### Install

```bash
pip install parking-availability-library==0.1.0
```

### Purpose

The custom library is used for:

* booking conflict detection
* available slot filtering
* slot recommendation
* occupancy rate calculation

---

## How to Test the Application

### User Testing

1. Register a new user
2. Login as user
3. Create a reservation
4. View own bookings
5. Edit reservation
6. Cancel reservation

### Admin Testing

1. Login as admin
2. Add parking slots
3. Edit parking slots
4. Manage users
5. View all reservations

### SNS Testing

1. Create a reservation
2. Cancel a reservation
3. Check email inbox for SNS notifications

### Lambda Testing

1. Create a reservation with a short end time
2. Wait for scheduled Lambda execution
3. Check if reservation becomes expired
4. Check if slot becomes available again

### Custom Library Testing

1. Try creating overlapping reservations
2. Confirm conflict is blocked
3. Check availability behavior
4. Confirm recommendation works

---

## Important Notes

* Admin-only pages are protected
* Users can only view and manage their own reservations
* SNS requires valid AWS credentials or EC2 IAM role
* Lambda must be configured separately in AWS
* S3, SNS, and Lambda require correct AWS region and resource configuration

---

## Deployment Notes

Before deploying to EC2, exclude these folders/files from upload if not needed:

* `dist/`
* `parking_availability_library.egg-info/`
* `parking_availability_library_backup/`
* `__pycache__/`

Keep these for deployment:

* `app.py`
* `config.py`
* `requirements.txt`
* `.env`
* `models/`
* `routes/`
* `templates/`
* `static/`
* `utils/`

---

## Author

Koka Divya Sai Priyanka

---

## License

This project is developed for academic coursework and demonstration purposes.