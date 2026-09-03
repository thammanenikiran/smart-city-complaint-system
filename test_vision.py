from services.vision_service import analyze_complaint_image


image_path = r"test_images\damage.jpg"


result = analyze_complaint_image(image_path)


print("\n================================")
print("GEMINI VISION RESULT")
print("================================")

print("Issue:", result["issue"])
print("Severity:", result["severity"])
print("Department:", result["department"])
print("Description:", result["description"])
print("Confidence:", result["confidence"])

print("================================")