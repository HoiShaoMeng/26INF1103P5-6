def get_user_input():

    # 1. Identify expected input types
    # All inputs are expected to be strings.

    reporter_name = input("Enter reporter name: ")
    report_datetime = input("Enter date/time reported: ")
    sender_email = input("Enter sender email: ")
    sender_name = input("Enter sender display name: ")
    subject = input("Enter email subject: ")
    body = input("Enter email body: ")
    attachment_filenames = input("Enter attachment filenames: ")
    attachment_extensions = input("Enter attachment file extensions: ")

    # 2. Validate user input

    if reporter_name == "":
        print("Invalid input: Reporter name cannot be empty.")
        return None

    if report_datetime == "":
        print("Invalid input: Date/time reported cannot be empty.")
        return None

    if sender_email == "":
        print("Invalid input: Sender email cannot be empty.")
        return None

    if "@" not in sender_email:
        print("Invalid input: Sender email must contain '@'.")
        return None

    if sender_name == "":
        print("Invalid input: Sender display name cannot be empty.")
        return None

    if subject == "":
        print("Invalid input: Email subject cannot be empty.")
        return None

    if body == "":
        print("Invalid input: Email body cannot be empty.")
        return None

    if attachment_filenames == "":
        print("Invalid input: Attachment filenames cannot be empty.")
        return None

    if attachment_extensions == "":
        print("Invalid input: Attachment file extensions cannot be empty.")
        return None

    # 3. Handle invalid input
    # Invalid input is rejected by returning None.

    return {
        "reporter_name": reporter_name,
        "report_datetime": report_datetime,
        "sender_email": sender_email,
        "sender_name": sender_name,
        "subject": subject,
        "body": body,
        "attachment_filenames": attachment_filenames,
        "attachment_extensions": attachment_extensions
    }
