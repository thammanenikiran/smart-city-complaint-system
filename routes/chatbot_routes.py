from flask import Blueprint, render_template, request, jsonify
from models.complaint import Complaint
import re


chatbot_bp = Blueprint(
    "chatbot",
    __name__,
    url_prefix="/chatbot"
)


# ---------------------------------------------------------
# CHATBOT PAGE
# ---------------------------------------------------------

@chatbot_bp.route("/")
def chatbot():
    return render_template("citizen/chatbot.html")


# ---------------------------------------------------------
# CHATBOT API
# ---------------------------------------------------------

@chatbot_bp.route("/ask", methods=["POST"])
def ask():

    data = request.get_json()

    if not data:
        return jsonify({
            "reply": "Please enter a question."
        })

    message = data.get("message", "").strip()

    if not message:
        return jsonify({
            "reply": "Please type your question."
        })

    text = message.lower()


    # -----------------------------------------------------
    # 1. GREETING
    # -----------------------------------------------------

    if any(word in text for word in [
        "hello",
        "hi",
        "hey",
        "good morning",
        "good afternoon",
        "good evening"
    ]):

        reply = (
            "Hello! 👋 I am the Smart City Citizen Help Assistant.<br><br>"
            "I can help you with:<br>"
            "• 📝 Submit a complaint<br>"
            "• 🔍 Track a complaint using Complaint ID<br>"
            "• 📊 Check complaint status<br>"
            "• 🏢 Find the responsible department<br>"
            "• ⚡ Understand complaint priority<br>"
            "• ℹ️ Understand the complaint process<br><br>"
            "For example, you can ask:<br>"
            "<b>Track complaint 22</b>"
        )

        return jsonify({"reply": reply})


    # -----------------------------------------------------
    # 2. TRACK COMPLAINT USING ID
    # -----------------------------------------------------

    # Find a number in the user's message
    id_match = re.search(r"\b(?:complaint\s*)?(?:id\s*)?#?\s*(\d+)\b", text)

    if id_match and any(word in text for word in [
        "track",
        "check",
        "status",
        "complaint",
        "progress"
    ]):

        complaint_id = int(id_match.group(1))

        complaint = Complaint.query.filter_by(
            complaint_id=complaint_id
        ).first()

        if not complaint:

            reply = (
                f"❌ I could not find Complaint <b>#{complaint_id}</b>.<br><br>"
                "Please check the Complaint ID and try again.<br><br>"
                "Example: <b>Track complaint [Complaint ID]</b>"
            )

            return jsonify({"reply": reply})


        # Get values safely
        status = getattr(complaint, "status", None) or "Not Available"

        priority = getattr(
            complaint,
            "priority",
            None
        ) or "Not Available"

        title = getattr(
            complaint,
            "title",
            None
        ) or "Complaint"


        # Try to get department information
        department_name = None

        department = getattr(
            complaint,
            "department",
            None
        )

        if department:

            department_name = getattr(
                department,
                "department_name",
                None
            )

            if not department_name:

                department_name = getattr(
                    department,
                    "name",
                    None
                )


        if not department_name:

            department_name = "Assigned Department"


        reply = (
            f"🔍 <b>Complaint #{complaint_id}</b><br><br>"
            f"📝 <b>Complaint:</b> {title}<br>"
            f"📊 <b>Status:</b> {status}<br>"
            f"⚡ <b>Priority:</b> {priority}<br>"
            f"🏢 <b>Department:</b> {department_name}<br><br>"
        )


        # Status explanation
        status_lower = str(status).lower()

        if "open" in status_lower:

            reply += (
                "⏳ Your complaint has been received and is waiting "
                "for further processing."
            )

        elif "progress" in status_lower:

            reply += (
                "🔧 Your complaint is currently being worked on "
                "by the assigned officer."
            )

        elif "resolved" in status_lower:

            reply += (
                "✅ Your complaint has been resolved."
            )

        elif "closed" in status_lower:

            reply += (
                "✔️ Your complaint has been completed and closed."
            )

        else:

            reply += (
                "ℹ️ Please check the complaint details for the latest update."
            )


        return jsonify({"reply": reply})


    # -----------------------------------------------------
    # 3. HOW TO SUBMIT COMPLAINT
    # -----------------------------------------------------

    if (
        ("submit" in text and "complaint" in text)
        or "report a problem" in text
        or "register complaint" in text
        or "create complaint" in text
    ):

        reply = (
            "📝 <b>How to submit a complaint:</b><br><br>"
            "1️⃣ Go to your <b>Citizen Dashboard</b>.<br>"
            "2️⃣ Click <b>Submit Complaint</b>.<br>"
            "3️⃣ Enter the complaint title and description.<br>"
            "4️⃣ You can upload an <b>image or video</b> of the problem.<br>"
            "5️⃣ Submit the complaint.<br><br>"
            "🤖 The system will automatically analyze your complaint "
            "using AI/NLP and identify the appropriate department."
        )

        return jsonify({"reply": reply})


    # -----------------------------------------------------
    # 4. HOW TO TRACK
    # -----------------------------------------------------

    if (
        "how to track" in text
        or "track my complaint" in text
        or "where can i track" in text
        or "how can i track" in text
        or "check my complaint" in text
    ):

        reply = (
            "🔍 <b>How to track your complaint:</b><br><br>"
            "You have two easy options:<br><br>"
            "1️⃣ <b>Chatbot:</b> Type "
            "<b>Track complaint + Complaint ID</b>.<br>"
            "Example: <b>Track complaint 22</b><br><br>"
            "2️⃣ <b>Citizen Dashboard:</b> Click "
            "<b>Track Complaint</b> and enter your Complaint ID.<br><br>"
            "I can directly check the complaint details for you "
            "when you provide the Complaint ID."
        )

        return jsonify({"reply": reply})


    # -----------------------------------------------------
    # 5. STATUS INFORMATION
    # -----------------------------------------------------

    if (
        "what is status" in text
        or "status meaning" in text
        or "what does open mean" in text
        or "what does in progress mean" in text
        or "what does resolved mean" in text
        or "complaint status" in text
    ):

        reply = (
            "📊 <b>Complaint Status Guide:</b><br><br>"
            "🟡 <b>Open:</b> Complaint has been received and is waiting "
            "for processing.<br><br>"
            "🔵 <b>In Progress:</b> An officer is currently working "
            "on the complaint.<br><br>"
            "🟢 <b>Resolved:</b> The reported problem has been fixed.<br><br>"
            "⚫ <b>Closed:</b> The complaint process has been completed."
        )

        return jsonify({"reply": reply})


    # -----------------------------------------------------
    # 6. ROADS
    # -----------------------------------------------------

    if any(word in text for word in [
        "pothole",
        "damaged road",
        "road problem",
        "road damage",
        "crosswalk"
    ]):

        reply = (
            "🛣️ Road-related complaints such as potholes, "
            "damaged roads and crosswalk problems are handled "
            "by the <b>Roads Department</b>."
        )

        return jsonify({"reply": reply})


    # -----------------------------------------------------
    # 7. SANITATION
    # -----------------------------------------------------

    if any(word in text for word in [
        "garbage",
        "waste",
        "overflowing bin",
        "dustbin",
        "sanitation"
    ]):

        reply = (
            "🗑️ Garbage collection, waste disposal and overflowing "
            "bins are handled by the <b>Sanitation Department</b>."
        )

        return jsonify({"reply": reply})


    # -----------------------------------------------------
    # 8. WATER
    # -----------------------------------------------------

    if any(word in text for word in [
        "water",
        "water leak",
        "water leakage",
        "no water",
        "pipe leak"
    ]):

        reply = (
            "💧 Water leakage and water supply complaints are handled "
            "by the <b>Water Supply Department</b>."
        )

        return jsonify({"reply": reply})


    # -----------------------------------------------------
    # 9. ELECTRICAL
    # -----------------------------------------------------

    if any(word in text for word in [
        "streetlight",
        "street light",
        "electricity",
        "electrical pole",
        "light not working"
    ]):

        reply = (
            "💡 Streetlights and electrical infrastructure complaints "
            "are handled by the <b>Electrical Department</b>."
        )

        return jsonify({"reply": reply})


    # -----------------------------------------------------
    # 10. TRAFFIC
    # -----------------------------------------------------

    if any(word in text for word in [
        "traffic",
        "traffic signal",
        "signal",
        "traffic sign"
    ]):

        reply = (
            "🚦 Traffic signals and traffic sign complaints are handled "
            "by the <b>Traffic Department</b>."
        )

        return jsonify({"reply": reply})


    # -----------------------------------------------------
    # 11. PARKS
    # -----------------------------------------------------

    if any(word in text for word in [
        "tree",
        "fallen tree",
        "park",
        "garden"
    ]):

        reply = (
            "🌳 Fallen trees, parks and garden-related complaints "
            "are handled by the <b>Parks and Gardens Department</b>."
        )

        return jsonify({"reply": reply})


    # -----------------------------------------------------
    # 12. GENERAL HELP
    # -----------------------------------------------------

    if (
        "help" in text
        or "what can you do" in text
        or "what can i ask" in text
    ):

        reply = (
            "🤖 <b>I can help you with:</b><br><br>"
            "📝 Submit a complaint<br>"
            "🔍 Track a complaint using its ID<br>"
            "📊 Check complaint status<br>"
            "🏢 Find the responsible department<br>"
            "⚡ Understand complaint priority<br>"
            "ℹ️ Explain the complaint process<br><br>"
            "Try asking:<br>"
            "• <b>Track complaint 22</b><br>"
            "• <b>How do I submit a complaint?</b><br>"
            "• <b>Which department handles potholes?</b>"
        )

        return jsonify({"reply": reply})


    # -----------------------------------------------------
    # 13. UNKNOWN QUESTION
    # -----------------------------------------------------

    reply = (
        "🤖 I can help you with Smart City complaints.<br><br>"
        "Try asking something like:<br>"
        "• <b>How do I submit a complaint?</b><br>"
        "• <b>Track complaint [Complaint ID]</b><br>"
        "• <b>What is the status of complaint [Complaint ID]?</b><br>"
        "• <b>Which department handles potholes?</b><br>"
        "• <b>My garbage bin is overflowing</b><br>"
        "• <b>Street light is not working</b>"
    )

    return jsonify({"reply": reply})