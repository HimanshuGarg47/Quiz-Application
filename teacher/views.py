from django.shortcuts import render, redirect, reverse
from . import forms
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from datetime import date, timedelta
from quiz import models as QMODEL
from student import models as SMODEL
from quiz import forms as QFORM
import numpy as np
from sklearn.cluster import KMeans
from django.db.models import Avg
from student.models import Student
from quiz.models import Course, Result

import numpy as np
import pandas as pd
from django.core.files.storage import default_storage
from django.conf import settings

import os
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile


# for showing signup/login button for teacher
def teacherclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect("afterlogin")
    return render(request, "teacher/teacherclick.html")


def teacher_signup_view(request):
    userForm = forms.TeacherUserForm()
    teacherForm = forms.TeacherForm()
    mydict = {"userForm": userForm, "teacherForm": teacherForm}
    if request.method == "POST":
        userForm = forms.TeacherUserForm(request.POST)
        teacherForm = forms.TeacherForm(request.POST, request.FILES)
        if userForm.is_valid() and teacherForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            teacher = teacherForm.save(commit=False)
            teacher.user = user
            teacher.save()
            my_teacher_group = Group.objects.get_or_create(name="TEACHER")
            my_teacher_group[0].user_set.add(user)
        return HttpResponseRedirect("teacherlogin")
    return render(request, "teacher/teachersignup.html", context=mydict)


def is_teacher(user):
    return user.groups.filter(name="TEACHER").exists()


@login_required(login_url="teacherlogin")
@user_passes_test(is_teacher)
def teacher_dashboard_view(request):
    dict = {
        "total_course": QMODEL.Course.objects.all().count(),
        "total_question": QMODEL.Question.objects.all().count(),
        "total_student": SMODEL.Student.objects.all().count(),
    }
    return render(request, "teacher/teacher_dashboard.html", context=dict)


@login_required(login_url="teacherlogin")
@user_passes_test(is_teacher)
def teacher_exam_view(request):
    return render(request, "teacher/teacher_exam.html")


@login_required(login_url="teacherlogin")
@user_passes_test(is_teacher)
def teacher_add_exam_view(request):
    courseForm = QFORM.CourseForm()
    if request.method == "POST":
        courseForm = QFORM.CourseForm(request.POST)
        if courseForm.is_valid():
            courseForm.save()
        else:
            print("form is invalid")
        return HttpResponseRedirect("/teacher/teacher-view-exam")
    return render(request, "teacher/teacher_add_exam.html", {"courseForm": courseForm})


@login_required(login_url="teacherlogin")
@user_passes_test(is_teacher)
def teacher_view_exam_view(request):
    courses = QMODEL.Course.objects.all()
    return render(request, "teacher/teacher_view_exam.html", {"courses": courses})


@login_required(login_url="teacherlogin")
@user_passes_test(is_teacher)
def delete_exam_view(request, pk):
    course = QMODEL.Course.objects.get(id=pk)
    course.delete()
    return HttpResponseRedirect("/teacher/teacher-view-exam")


@login_required(login_url="adminlogin")
def teacher_question_view(request):
    return render(request, "teacher/teacher_question.html")


from sklearn.preprocessing import MinMaxScaler

from sklearn.preprocessing import MinMaxScaler
import numpy as np

def calculate_student_insights():
    # Step 1: Extract data
    students = Student.objects.all()
    courses = Course.objects.all()

    # Build data matrix (rows: students, columns: subjects)
    student_scores = []
    for student in students:
        scores = []
        for course in courses:
            avg_score = (
                Result.objects.filter(student=student, exam=course).aggregate(
                    Avg("marks")
                )["marks__avg"]
                or 0
            )
            scores.append(avg_score)
        student_scores.append(scores)

    # Step 2: Normalize data
    data_matrix = np.array(student_scores)
    scaler = MinMaxScaler()  # Use MinMaxScaler to normalize data between 0 and 1
    normalized_data = scaler.fit_transform(data_matrix)

    # Step 3: Define Performance Groups based on quantiles
    performance_groups = []
    avg_scores = np.mean(normalized_data, axis=1)  # Calculate the average score for each student
    top_achiever_threshold = np.percentile(avg_scores, 75)  # Top 25% for Top Achievers
    struggling_learner_threshold = np.percentile(avg_scores, 25)  # Bottom 25% for Struggling Learners

    for score in avg_scores:
        if score >= top_achiever_threshold:
            performance_groups.append("Top Achievers")  # High performers
        elif score <= struggling_learner_threshold:
            performance_groups.append("Struggling Learners")  # Low performers
        else:
            performance_groups.append("Average Performers")  # Medium performers

    # Step 4: Prepare insights
    insights = []
    weak_subjects_per_student = {}
    weak_students_per_topic = {course.course_name: [] for course in courses}

    # Store pie charts for each student
    student_pie_charts = {}

    for i, student in enumerate(students):
        performance_group = performance_groups[i]
        weak_subjects = [
            courses[j].course_name
            for j in range(len(courses))
            if normalized_data[i][j] < 0.5  # Subject is weak if normalized score < 50%
        ]

        insights.append(
            {
                "student": student.get_name,
                "performance_group": performance_group,
                "weak_subjects": weak_subjects,
            }
        )

        weak_subjects_per_student[student.get_name] = weak_subjects
        for weak_subject in weak_subjects:
            weak_students_per_topic[weak_subject].append(student.get_name)

        # Generate a pie chart for each student
        pie_chart = generate_student_pie_chart(student, courses, student_scores[i])
        student_pie_charts[student.get_name] = pie_chart

    plot_images = generate_performance_plots(
        students,
        courses,
        normalized_data,
        weak_subjects_per_student,
        weak_students_per_topic,
    )

    return insights, plot_images, student_pie_charts






def generate_student_pie_chart(student, courses, scores):
    # Generate pie chart
    labels = [course.course_name for course in courses]
    fig, ax = plt.subplots()
    ax.pie(scores, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.axis("equal")  # Draw pie as a circle
    plt.title(f"{student.get_name}'s Performance by Course")

    # Define file path in your app's media folder
    filename = f"{student.get_name}_performance_pie.png"
    file_path = os.path.join(settings.MEDIA_ROOT, "charts", filename)

    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Save plot as an image
    plt.savefig(file_path, format="png")
    plt.close()

    return f"{settings.MEDIA_URL}charts/{filename}"


def generate_performance_plots(
    students,
    courses,
    normalized_data,
    weak_subjects_per_student,
    weak_students_per_topic,
):
    # 1. Overall Performance Bar Plot (Average Scores in Each Course)
    avg_scores = np.mean(normalized_data, axis=0)  # Average score per course
    plt.figure(figsize=(16, 6))
    sns.barplot(x=[course.course_name for course in courses], y=avg_scores)
    plt.title("Average Scores per Course")
    plt.xlabel("Courses")
    plt.ylabel("Average Score")
    overall_performance_plot = save_plot_to_image()

    # 2. Group Performance Comparison (High, Medium, Low Performers)
    # Get the average score of each student across all courses
    student_avg_scores = np.mean(normalized_data, axis=1)

    # Create indices for students based on their average score
    sorted_student_indices = np.argsort(student_avg_scores)

    # Divide students into three roughly equal groups
    num_students = len(students)
    group_size = num_students // 3
    high_group_indices = sorted_student_indices[:group_size]
    medium_group_indices = sorted_student_indices[group_size : 2 * group_size]
    low_group_indices = sorted_student_indices[2 * group_size :]

    # Collect student scores for each group
    group_performance = {"High": [], "Medium": [], "Low": []}

    for i in high_group_indices:
        group_performance["High"].append(normalized_data[i])
    for i in medium_group_indices:
        group_performance["Medium"].append(normalized_data[i])
    for i in low_group_indices:
        group_performance["Low"].append(normalized_data[i])

    # Ensure that all groups have the same number of elements
    performance_df = pd.DataFrame(
        {
            "High": [score for group in group_performance["High"] for score in group],
            "Medium": [
                score for group in group_performance["Medium"] for score in group
            ],
            "Low": [score for group in group_performance["Low"] for score in group],
        }
    )

    # Create a boxplot using Seaborn
    plt.figure(figsize=(16, 6))
    sns.boxplot(data=performance_df)
    plt.title("Group Performance Comparison")
    plt.xlabel("Performance Group")
    plt.ylabel("Normalized Score")
    group_comparison_plot = save_plot_to_image()

    # 3. Weak Students per Topic (Bar Plot)
    weak_students_count = {
        topic: len(students) for topic, students in weak_students_per_topic.items()
    }
    plt.figure(figsize=(16, 6))
    sns.barplot(
        x=list(weak_students_count.keys()), y=list(weak_students_count.values())
    )
    plt.title("Number of Weak Students per Topic")
    plt.xlabel("Topic")
    plt.ylabel("Number of Weak Students")
    weak_students_plot = save_plot_to_image()

    return {
        "overall_performance": overall_performance_plot,
        "group_comparison": group_comparison_plot,
        "weak_students": weak_students_plot,
    }


def save_plot_to_image():
    """Helper function to save the current plot to an image."""
    img_buf = BytesIO()
    plt.savefig(img_buf, format="png")
    img_buf.seek(0)
    img_file = InMemoryUploadedFile(
        img_buf, None, "plot.png", "image/png", img_buf.getbuffer().nbytes, None
    )
    plt.close()  # Close the plot to avoid overlap
    return img_file


from django.shortcuts import render


@login_required(login_url="teacherlogin")
def teacher_insight(request):
    insights, plot_images, pie_plot = calculate_student_insights()
    return render(
        request,
        "teacher/teacher_insight.html",
        {"insights": insights, "plot_images": plot_images, "pie_plot": pie_plot},
    )


@login_required(login_url="teacherlogin")
@user_passes_test(is_teacher)
def teacher_add_question_view(request):
    questionForm = QFORM.QuestionForm()
    if request.method == "POST":
        questionForm = QFORM.QuestionForm(request.POST)
        if questionForm.is_valid():
            question = questionForm.save(commit=False)
            course = QMODEL.Course.objects.get(id=request.POST.get("courseID"))
            question.course = course
            question.save()
        else:
            print("form is invalid")
        return HttpResponseRedirect("/teacher/teacher-view-question")
    return render(
        request, "teacher/teacher_add_question.html", {"questionForm": questionForm}
    )


@login_required(login_url="teacherlogin")
@user_passes_test(is_teacher)
def teacher_view_question_view(request):
    courses = QMODEL.Course.objects.all()
    return render(request, "teacher/teacher_view_question.html", {"courses": courses})


@login_required(login_url="teacherlogin")
@user_passes_test(is_teacher)
def see_question_view(request, pk):
    questions = QMODEL.Question.objects.all().filter(course_id=pk)
    return render(request, "teacher/see_question.html", {"questions": questions})


@login_required(login_url="teacherlogin")
@user_passes_test(is_teacher)
def remove_question_view(request, pk):
    question = QMODEL.Question.objects.get(id=pk)
    question.delete()
    return HttpResponseRedirect("/teacher/teacher-view-question")
