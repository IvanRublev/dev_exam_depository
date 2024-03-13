import re


def test_pass_submission_has_verification_code_generated(build_models_student, build_models_submission):
    student = build_models_student()
    submission = build_models_submission({"student_id": student.id})
    assert re.match(r"^[a-z0-9]{9}$", submission.verification_code)
