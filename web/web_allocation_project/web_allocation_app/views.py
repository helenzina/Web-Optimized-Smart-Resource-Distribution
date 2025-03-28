import json
import os
from django.shortcuts import redirect, render, HttpResponse
import pandas as pd
from allocation.app.app import App
from allocation.student_course.course import Course
from allocation.student_course.student import Student


# Create your views here.

def json_serialization(request, app_obj):
    """This method converts class objects to json files and
    returns the selected students."""

    # for selected students table display
    columns = ["Fullname", "AEM", "GPA", "Selections"]
    data = {c: [] for c in columns}

    for student in app_obj.students:
        data["Fullname"].append(student.fullname)
        data["AEM"].append(student.student_id)
        data["GPA"].append(student.gpa)

        temp = {p: c for c, p in student.preferences.items()}
        temp = dict(sorted(temp.items()))

        course_choices = [c for p, c in temp.items()]

        data["Selections"].append(", ".join(map(str, course_choices)))

    selected_students = pd.DataFrame(data)

    # converting class objects to json in session
    # to use in the allocation view (serialization)
    try:
        students_json = json.dumps(
            app_obj.students, default=lambda x: x.__dict__, indent=4
        )
        courses_json = json.dumps(
            app_obj.courses, default=lambda x: x.__dict__, indent=4
        )
        selected_students_json = selected_students.to_json(orient='records')
    except Exception as e:
        return HttpResponse(
            f"Error while serializing the json files: {str(e)}", status=404
        )

    request.session["students"] = students_json
    request.session["courses"] = courses_json
    request.session["selected_students"] = selected_students_json
    request.session["has_students"] = not selected_students.empty

    return selected_students


def home(request):
    if request.method == "POST" and "files-submit" in request.POST:
        students_data = request.FILES.get("students")
        courses_data = request.FILES.get("courses")
        students_selections_data = request.FILES.get("students_selections")
        sem = request.POST.get("sem")

        students_ext = os.path.splitext(students_data.name)[-1].lower()
        courses_ext = os.path.splitext(courses_data.name)[-1].lower()
        students_selections_ext = os.path.splitext(students_selections_data.name)[
            -1
        ].lower()

        extensions = [students_ext, courses_ext, students_selections_ext]
        for e in extensions:
            if e not in [".xlsx", ".xls"]:
                return render(
                    request,
                    "home.html",
                    {
                        "error_message": "Each file should have an excel's file extension (.xlsx or .xls)."
                    },
                )

        try:
            students_sheet_names = pd.ExcelFile(students_data).sheet_names
            courses_sheet_name = pd.ExcelFile(courses_data).sheet_names[0]
            students_selections_sheet_name = pd.ExcelFile(
                students_selections_data
            ).sheet_names[0]
        except Exception as e:
            return HttpResponse(
                f"Error reading an excel file: {str(e)}", status=404
            )

        app_obj = App(
            students_data,
            students_sheet_names,
            courses_data,
            courses_sheet_name,
            students_selections_data,
            students_selections_sheet_name,
            int(sem),
            0,
            0,
        )

        selected_students = json_serialization(request, app_obj)

        context = {
            "selected_students": selected_students,
            "has_students": request.session.get("has_students", False),
        }

        return render(request, "allocation.html", context)

    if request.method == "POST" and "allocation-submit" in request.POST:
        return redirect("allocation")
    else:
        return render(request, "home.html")


def get_context_from_session(request):
    selected_students = json.loads(request.session.get("selected_students", "[]"))
    allocated_students = json.loads(request.session.get("allocated_students", "[]"))
    return {
        "selected_students": selected_students,
        "has_students": request.session.get("has_students", False),
        "allocated_students": allocated_students,
        "has_allocated_students": True if allocated_students else False,
    }


def json_deserialization(request):
    """This method converts json files to class objects and
    returns the App object and the context."""

    context = get_context_from_session(request)
    context.update({
        "selected_students": pd.DataFrame(context["selected_students"]),
        "allocated_students": pd.DataFrame(context["allocated_students"]),
    })

    students_json = request.session.get("students")
    courses_json = request.session.get("courses")

    if not students_json or not courses_json:
        return HttpResponse("Something went wrong with the json files.", status=404)

    students_dicts = json.loads(students_json)
    class_object_students = []
    for student in students_dicts:
        student_obj = Student()
        for k, v in student.items():
            if k == "preferences":
                v = {int(p): c for p, c in v.items()}

            setattr(student_obj, k, v)

        class_object_students.append(student_obj)

    courses_dicts = json.loads(courses_json)
    class_object_courses = []
    for course in courses_dicts:
        course_obj = Course()
        for k, v in course.items():
            if k == "course_id":
                v = int(v)

            setattr(course_obj, k, v)

        class_object_courses.append(course_obj)

    new_app = App()
    new_app.students = class_object_students
    new_app.courses = class_object_courses
    return new_app, context


def allocation(request):
    new_app, context = json_deserialization(request)

    if request.method == "POST" and "allocation-submit" in request.POST:
        min_stud = int(request.POST.get("min_stud", 0))
        max_stud = int(request.POST.get("max_stud", 0))

        if min_stud < max_stud and max_stud != 0:
            for course in new_app.courses:
                course.min_students = min_stud
                course.max_students = max_stud

            allocated_students = new_app.run()
            if allocated_students is not None:
                has_allocated_students = not allocated_students.empty
                request.session["allocated_students"] = allocated_students.to_json(orient='records')
                request.session["has_allocated_students"] = has_allocated_students

                context.update({
                    "allocated_students": allocated_students,
                    "has_allocated_students": has_allocated_students,
                    "min_stud": min_stud,
                    "max_stud": max_stud,
                })

        if min_stud >= max_stud or max_stud == 0 or "has_allocated_students" not in request.session:
            error_message = "Infeasible solution. Please provide different min and max values."
            request.session["error_message"] = error_message

        context.update(
            {
                "min_stud": min_stud,
                "max_stud": max_stud,
                "error_message": request.session.get("error_message") if "error_message" in request.session else None,
            },
        )

    if request.method == "POST" and "allocation-download" in request.POST:
        allocation_download = request.POST.get("allocation-download")
        if allocation_download == "download_excel":
            new_app.write()


    return render(request, "allocation.html", context)
