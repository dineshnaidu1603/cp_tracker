import base64
import io

import matplotlib
import requests
from django.contrib.auth import login, logout
from django.shortcuts import redirect

matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from django.contrib.auth.hashers import make_password
from .models import CustomUser
from .forms import EmailAuthenticationForm  # Use custom login form
import datetime
from django.contrib.auth.decorators import login_required
from django.conf import settings

from django.shortcuts import render
from django.http import JsonResponse
from langchain_groq import ChatGroq

llm = ChatGroq(
    temperature=0,
    groq_api_key=settings.GROQ_API_KEY,
    model_name="llama-3.3-70b-versatile"
)


def chatbot(request):
    if request.method == "POST":
        user_message = request.POST.get("message", "")
        response = llm.invoke(user_message)
        return JsonResponse({"response": response.content})

    return render(request, "chart.html")


def register(request):
    if request.method == "POST":
        name = request.POST.get("name")
        password = request.POST.get("password")
        email = request.POST.get("email")
        year = request.POST.get("year")
        section = request.POST.get("section")
        leetcode = request.POST.get("leetcode")
        codechef = request.POST.get("codechef")
        hackerrank = request.POST.get("hackerrank")
        codeforces = request.POST.get("codeforces")

        # Check if email already exists
        if CustomUser.objects.filter(email=email).exists():
            return render(request, "register.html", {"error": "Email already exists."})

        # Create new user
        user = CustomUser.objects.create(
            username=name,
            email=email,
            password=make_password(password),  # Hash password before saving
            year=year,
            section=section,
            leetcode=leetcode,
            codechef=codechef,
            hackerrank=hackerrank,
            codeforces=codeforces
        )
        user.save()

        return redirect("login")  # Redirect to login page after successful registration

    return render(request, "register.html")


def login_view(request):
    if request.method == "POST":
        form = EmailAuthenticationForm(data=request.POST)  # Use custom form
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("dashboard")  # Redirect to dashboard upon successful login
    else:
        form = EmailAuthenticationForm()
    return render(request, "login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    username = request.user.leetcode  # Get LeetCode username from user model
    handle = request.user.codechef  # Get CodeChef username

    # ------------------ LeetCode Data Fetching ------------------
    leetcode_url = "https://leetcode.com/graphql"
    headers = {
        "Content-Type": "application/json",
        "x-csrftoken": "YOUR_CSRF_TOKEN",
        "cookie": "YOUR_COOKIES",
    }
    query = {
        "query": f"""
        {{
            matchedUser(username: "{username}") {{
                username
                submitStats: submitStatsGlobal {{
                    acSubmissionNum {{
                        difficulty
                        count
                    }}
                }}
            }}
        }}
        """
    }

    response = requests.post(leetcode_url, json=query, headers=headers)
    leetcode_data = response.json()

    # Check if valid response
    if "data" in leetcode_data and leetcode_data["data"]["matchedUser"]:
        ac_submission_data = leetcode_data["data"]["matchedUser"]["submitStats"]["acSubmissionNum"]
        difficulties = [item["difficulty"] for item in ac_submission_data]
        ac_counts = [item["count"] for item in ac_submission_data]
        total_ac = sum(ac_counts)  # Total Accepted Submissions
    else:
        difficulties, ac_counts, total_ac = [], [], 0

    # ---- LeetCode: Bar Chart ----
    plt.figure(figsize=(9, 6))
    bars = plt.bar(difficulties, ac_counts, color=['blue', 'green', 'orange', 'red'])

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval, yval, ha='center', va='bottom', fontsize=12,
                 fontweight='bold')

    plt.xlabel("Difficulty Level")
    plt.ylabel("Accepted Submissions")
    plt.title("Accepted Submissions per Difficulty")

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    leetcode_chart = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    plt.close()

    # ---- LeetCode: Total Submissions Display ----
    plt.figure(figsize=(9, 2))
    plt.text(0.5, 0.5, f"Total Accepted: {ac_counts[0]}", ha='center', va='center', fontsize=20, fontweight='bold',
             color='Red')
    plt.axis('off')

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    total_chart_url = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    plt.close()

    # ------------------ CodeChef Data Fetching ------------------
    if not handle:
        return render(request, "dashboard.html", {"error": "CodeChef username not set."})

    codechef_url = f"https://codechef-api.vercel.app/handle/{handle}"
    response = requests.get(codechef_url)

    if response.status_code != 200:
        return render(request, "dashboard.html", {"error": "Failed to fetch data from CodeChef API."})

    data = response.json()

    # Extract rating and stars
    user_rating = data.get("currentRating", "N/A")
    user_stars = data.get("stars", "N/A")

    # Check if rating data exists
    if "ratingData" not in data:
        return render(request, "dashboard.html", {"error": "No contest rating data available."})

    contest_data = data["ratingData"]

    # Extract contest details
    contest_dates = [
        datetime.datetime.strptime(f"{contest['getyear']}-{contest['getmonth']}-{contest['getday']}", "%Y-%m-%d")
        for contest in contest_data
    ]
    ratings = [int(contest["rating"]) for contest in contest_data]

    # ---- CodeChef: Rating Over Time (Line Chart) ----
    plt.figure(figsize=(10, 5))
    plt.plot(contest_dates, ratings, marker="o", linestyle="-", color="red", label="Rating")
    plt.xlabel("Date")
    plt.ylabel("Rating")
    plt.title(f"Rating Over Time - {handle}")
    plt.xticks(rotation=45)
    plt.grid()
    plt.legend()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    rating_chart = base64.b64encode(buf.getvalue()).decode("utf-8")
    buf.close()
    plt.close()

    # ---- CodeChef: Contests Per Year (Bar Chart) ----
    contest_counts = {}
    for date in contest_dates:
        year = date.year
        contest_counts[year] = contest_counts.get(year, 0) + 1

    plt.figure(figsize=(8, 5))
    plt.bar(contest_counts.keys(), contest_counts.values(), color="g")
    plt.xlabel("Year")
    plt.ylabel("Number of Contests")
    plt.title(f"Contests Participated Over Time - {handle}")
    plt.xticks(list(contest_counts.keys()))
    plt.grid(axis="y")

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    contest_chart = base64.b64encode(buf.getvalue()).decode("utf-8")
    buf.close()
    plt.close()

    return render(request, "dashboard.html", {
        "leetcode_chart": leetcode_chart,
        "total_chart_url": total_chart_url,
        "user_rating": user_rating,
        "user_stars": user_stars,
        "rating_chart": rating_chart,
        "contest_chart": contest_chart,
    })
