class Student:
    def __init__(self, *args):
        if len(args) == 0:
            pass
        else:
            self.student_id = args[0]
            self.fullname = args[1]
            self.gpa = None
            self.SCALING_FACTOR = 100
            self.scaled_gpa = None
            self.semester = args[2]
            self.preferences = {}
            self.courses_needed = args[3]
            self.passed_courses_on_sem8 = args[4]
            self.choices_remaining = args[5]
            self.courses_needed_remaining = self.courses_needed - self.passed_courses_on_sem8
            self.is_obligated = None

    # def __init__(self, student_id, fullname, semester, courses_needed, passed_courses_on_sem8, choices_remaining):
    #     self.student_id = student_id
    #     self.fullname = fullname
    #     self.gpa = None
    #     self.SCALING_FACTOR = 100
    #     self.scaled_gpa = None
    #     self.semester = semester
    #     self.preferences = {}
    #     self.courses_needed = courses_needed
    #     self.passed_courses_on_sem8 = passed_courses_on_sem8
    #     self.choices_remaining = choices_remaining
    #     self.courses_needed_remaining = self.courses_needed - self.passed_courses_on_sem8
    #     self.is_obligated = None

    def set_gpa(self, gpa):
        self.gpa = gpa
        self.scaled_gpa = int(self.gpa * self.SCALING_FACTOR)

    def set_preferences(self, preferences):
        self.preferences = preferences

    def set_is_obligated(self, is_obligated):
        self.is_obligated = is_obligated
