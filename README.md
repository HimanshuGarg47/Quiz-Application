# Django-Based Online Quiz Management System

A comprehensive online quiz management platform built with Django, featuring role-based access for **Admins**, **Teachers**, and **Students**. The project enables effective management, execution, and performance analysis of quizzes. With data-driven insights powered by machine learning, teachers can provide targeted support based on individual and class-wide performance metrics.

---

## 🧑‍💻 User Roles & Features

### **Admin**
- **Account Setup**: Created via command line.
- **Dashboard**: Displays total count of students, teachers, courses, and questions.
- **User Management**: Approve, update, or delete teachers, manage students, and view student marks.
- **Course & Exam Management**: Add, view, delete courses and questions, including options and correct answers.

### **Teacher**
- **Account Setup**: Requires admin approval after applying.
- **Dashboard**: Displays information on students, courses, and questions.
- **Course & Exam Management**: Manages courses and adds questions with detailed options and marks.

### **Student**
- **Account Setup**: Can self-register and log in without admin approval.
- **Dashboard**: Accesses available courses and questions.
- **Exam Attempts**: Can take quizzes multiple times with results available for each attempt.

**Note**: Admins are responsible for hiring teachers to manage courses and questions.

---

## 🛠️ Setup Instructions
```


### 1. Install Dependencies
Ensure you have **Python 3.7.6** and required dependencies:
```bash
git clone url
cd Quiz-Application

python -m venv .venv
.\.venv\Scripts\acitvate

python -m pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver

