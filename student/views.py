from django.shortcuts import render, redirect, reverse
from . import forms, models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from datetime import date, timedelta
from quiz import models as QMODEL
from teacher import models as TMODEL


import requests
from django.conf import settings


def get_related_videos(course_name):
    youtube_api_key = (
        settings.YOUTUBE_API_KEY
    )  # Store your API key in settings for security
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": "tutorial"
        + course_name
        + " full video",  # Use course name as search query
        "type": "video",
        "maxResults": 10,  # Limit the number of videos displayed
        "key": youtube_api_key,
    }
    response = requests.get(search_url, params=params)
    videos = response.json().get("items", [])

    # List to hold filtered videos
    filtered_videos = []

    for video in videos:
        video_title = video["snippet"]["title"]
        video_id = video["id"]["videoId"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        # Get the video details to check length
        video_details_url = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails&id={video_id}&key={youtube_api_key}"
        video_details_response = requests.get(video_details_url)
        video_details = video_details_response.json().get("items", [])[0]

        if video_details:
            # Extract the duration (in ISO 8601 format, e.g., "PT11M32S" for 11 minutes 32 seconds)
            video_duration = video_details["contentDetails"]["duration"]

            # Convert ISO 8601 duration to total minutes
            import isodate

            duration = isodate.parse_duration(video_duration)
            video_length_minutes = duration.total_seconds() / 60  # Convert to minutes

            # Check if the length is greater than 10 minutes
            if video_length_minutes > 10:
                # Add the video to the filtered list
                filtered_videos.append(
                    {
                        "title": video_title,
                        "video_id": video_id,
                        "url": video_url,
                        "thumbnail": video["snippet"]["thumbnails"]["high"]["url"],
                        "duration": video_length_minutes,
                    }
                )

    return filtered_videos[:5]
    # response = requests.get(search_url, params=params)
    # videos = []
    # if response.status_code == 200:
    #     results = response.json().get("items", [])
    #     for item in results:
    #         video_data = {
    #             "title": item["snippet"]["title"],
    #             "video_id": item["id"]["videoId"],
    #             "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
    #         }
    #         videos.append(video_data)
    # return videos


# for showing signup/login button for student
def studentclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect("afterlogin")
    return render(request, "student/studentclick.html")


def student_signup_view(request):
    userForm = forms.StudentUserForm()
    studentForm = forms.StudentForm()
    mydict = {"userForm": userForm, "studentForm": studentForm}
    if request.method == "POST":
        userForm = forms.StudentUserForm(request.POST)
        studentForm = forms.StudentForm(request.POST, request.FILES)
        if userForm.is_valid() and studentForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            student = studentForm.save(commit=False)
            student.user = user
            student.save()
            my_student_group = Group.objects.get_or_create(name="STUDENT")
            my_student_group[0].user_set.add(user)
        return HttpResponseRedirect("studentlogin")
    return render(request, "student/studentsignup.html", context=mydict)


def is_student(user):
    return user.groups.filter(name="STUDENT").exists()


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def student_dashboard_view(request):
    dict = {
        "total_course": QMODEL.Course.objects.all().count(),
        "total_question": QMODEL.Question.objects.all().count(),
    }
    return render(request, "student/student_dashboard.html", context=dict)


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def student_exam_view(request):
    courses = QMODEL.Course.objects.all()
    return render(request, "student/student_exam.html", {"courses": courses})


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def take_exam_view(request, pk):
    course = QMODEL.Course.objects.get(id=pk)
    related_videos = get_related_videos(course.course_name)
    total_questions = QMODEL.Question.objects.all().filter(course=course).count()
    questions = QMODEL.Question.objects.all().filter(course=course)
    total_marks = 0
    for q in questions:
        total_marks = total_marks + q.marks

    return render(
        request,
        "student/take_exam.html",
        {
            "course": course,
            "related_videos": related_videos,
            "total_questions": total_questions,
            "total_marks": total_marks,
        },
    )


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def start_exam_view(request, pk):
    course = QMODEL.Course.objects.get(id=pk)
    questions = QMODEL.Question.objects.all().filter(course=course)
    if request.method == "POST":
        pass
    response = render(
        request, "student/start_exam.html", {"course": course, "questions": questions}
    )
    response.set_cookie("course_id", course.id)
    return response


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def calculate_marks_view(request):
    if request.COOKIES.get("course_id") is not None:
        course_id = request.COOKIES.get("course_id")
        course = QMODEL.Course.objects.get(id=course_id)

        total_marks = 0
        questions = QMODEL.Question.objects.all().filter(course=course)
        for i in range(len(questions)):

            selected_ans = request.COOKIES.get(str(i + 1))
            actual_answer = questions[i].answer
            if selected_ans == actual_answer:
                total_marks = total_marks + questions[i].marks
        student = models.Student.objects.get(user_id=request.user.id)
        result = QMODEL.Result()
        result.marks = total_marks
        result.exam = course
        result.student = student
        result.save()

        return HttpResponseRedirect("view-result")


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def view_result_view(request):
    courses = QMODEL.Course.objects.all()
    return render(request, "student/view_result.html", {"courses": courses})


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def check_marks_view(request, pk):
    course = QMODEL.Course.objects.get(id=pk)
    student = models.Student.objects.get(user_id=request.user.id)
    results = QMODEL.Result.objects.all().filter(exam=course).filter(student=student)
    return render(request, "student/check_marks.html", {"results": results})


@login_required(login_url="studentlogin")
@user_passes_test(is_student)
def student_marks_view(request):
    courses = QMODEL.Course.objects.all()
    return render(request, "student/student_marks.html", {"courses": courses})
