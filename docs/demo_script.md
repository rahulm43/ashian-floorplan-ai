# ASHIAN – ASK YOUR FLOOR PLAN
## 5-Minute Video Demonstration Script & Presentation Guide

This script is structured for a comprehensive, professional video demonstration of the **ASHIAN Floor Plan AI** application for the RSF Ventures Private Limited Tech Intern Take-Home Task submission.

---

### Segment 1: Introduction & Architectural Overview (0:00 – 0:45)
- **Visual:** Open browser on the **Home Dashboard** (`http://localhost:8501`).
- **Speaker:** 
  > *"Hello, my name is [Your Name], presenting 'ASHIAN – Ask Your Floor Plan', an AI-powered architectural floor plan understanding and natural language question answering system. 
  > Floor plan blueprints contain complex spatial geometry that traditional language models cannot process directly without vision and spatial grounding. ASHIAN bridges this gap by extracting architectural entities—rooms, doors, windows, walls, and inter-room connectivity—storing them in a normalized relational SQLite database, and answering natural language questions grounded strictly in database evidence with zero hallucination."*
- **Action:** Point out live metrics: Total Floor Plans (54), Extracted Rooms (433), Doors (416), Windows (326), and Inter-room links (519).

---

### Segment 2: Computer Vision Extraction & Floor Plan Explorer (0:45 – 1:45)
- **Visual:** Navigate to **📐 Floor Plan Explorer** tab.
- **Speaker:**
  > *"Let's look at the computer vision extraction pipeline. We inspected the Kaggle CVC-FPP floor plan dataset and identified the exact semantic segmentation color classes: coral orange for rooms, ice blue for walls, lime green for doors, and golden amber for windows.
  > Let's select Floor Plan 10. In the 3-Panel Inspection view, you can see the original blueprint on the left, the semantic mask in the center, and our extracted annotations on the right. 
  > The pipeline performs connected component analysis, morphological filtering, and Douglas-Peucker polygonal boundary approximation. Notice each room has its centroid, bounding box, and pixel area extracted without guessing metric dimensions. Furthermore, through spatial dilation of door components, our system determines which rooms are physically accessible to each other."*
- **Action:** Toggle between "Annotated Overlay", "3-Panel Inspection", and the extracted data tables for Rooms, Doors, Windows, and Connections.

---

### Segment 3: AI Assistant Live Q&A Demonstration (1:45 – 3:30)
- **Visual:** Navigate to **💬 AI Q&A Assistant** tab.
- **Speaker:**
  > *"Now let's test our AI Question Answering Assistant. Every single answer must provide verifiable SQL evidence."*

#### Question 1 (Room Count):
- **User Prompt:** `"How many rooms does plan 12 have?"`
- **Assistant Response:** *"Plan 12 contains 8 extracted rooms."*
- **Evidence:** Expand SQL expander: `SELECT COUNT(*) AS room_count FROM rooms WHERE plan_id = 12;`

#### Question 2 (Largest Room):
- **User Prompt:** `"What is the largest room in plan 10?"`
- **Assistant Response:** *"The largest room in plan 10 is Room 5 (Room ID 10005) with a segmented area of 582,751 pixels."*
- **Evidence:** Show executed SQL ordering by `area_pixels DESC LIMIT 1`.

#### Question 3 (Door Threshold Query):
- **User Prompt:** `"Which plans have more than 15 doors?"`
- **Assistant Response:** Shows sorted plans: Plan 20 (20 doors), Plan 30 (17 doors), Plan 31 (17 doors)...
- **Evidence:** `SELECT plan_id, COUNT(*) FROM doors GROUP BY plan_id HAVING COUNT(*) > 15;`

#### Question 4 (Rooms Without Windows):
- **User Prompt:** `"Which room in plan 4 has no windows?"`
- **Assistant Response:** *"In plan 4, the following room(s) have no windows: Room 3 (ID 4003), Room 6 (ID 4006), Room 8 (ID 4008)."*
- **Evidence:** `SELECT room_id, category FROM rooms WHERE plan_id = 4 AND window_count = 0;`

#### Question 5 (Average Calculation):
- **User Prompt:** `"What is the average number of rooms across all plans?"`
- **Assistant Response:** *"The average number of rooms across all processed floor plans is 8.02."*
- **Evidence:** `SELECT ROUND(AVG(total_rooms), 2) FROM plans;`

#### Question 6 (Room Areas):
- **User Prompt:** `"What are the areas of all rooms in plan 10?"`
- **Assistant Response:** Itemized pixel areas for Rooms 1 through 10. Emphasize: *"Notice the assistant reports pixel measurements and does not fabricate square metres."*

#### Question 7 (Inter-Room Connectivity):
- **User Prompt:** `"Which rooms are connected through doors in plan 10?"`
- **Assistant Response:** Lists active links: Room 10003 <-> Room 10005 via Door 10002, etc.

#### Question 8 (Missing Information / Limitations):
- **User Prompt:** `"What information is unavailable in this floor plan?"`
- **Assistant Response:** Clear itemization of missing metric scale, structural load, ceiling height, and MEP specifications.

#### Question 9 (Negative Test – Out of Domain):
- **User Prompt:** `"What color are the walls painted in plan 12?"`
- **Assistant Response:** *"I cannot determine this from the available floor plan data. Architectural attributes such as 'color' are not recorded in this dataset."*

#### Question 10 (Negative Test – Invalid Plan ID):
- **User Prompt:** `"How many rooms does plan 9999 have?"`
- **Assistant Response:** *"Plan 9999 was not found in the database. Available plans include: 1, 2, 3, 4, 10, 12..."*

---

### Segment 4: Data Analytics & Evaluation Benchmark (3:30 – 4:30)
- **Visual:** Navigate to **📊 Data Analysis** and then **🏆 Evaluation Benchmark**.
- **Speaker:**
  > *"Under Data Analysis, we provide interactive visual distributions of room counts, door-to-window ratios, and room area curves across the entire dataset.
  > Under Evaluation Benchmark, we implemented the Stand-Out Feature: Option A. We designed an automated benchmark runner with 22 test questions across all required categories. Every expected answer was derived directly from live database records. 
  > The system achieved 100% benchmark accuracy, with full SQL safety validation blocking all destructive statements."*

---

### Segment 5: Testing, Code Quality & Conclusion (4:30 – 5:00)
- **Visual:** Show terminal running `pytest -v tests/`.
- **Speaker:**
  > *"Our complete codebase is backed by 9 unit and integration tests covering computer vision extraction, database cascading and transactions, and SQL security filters, achieving a 100% pass rate.
  > Thank you for reviewing ASHIAN – Ask Your Floor Plan. All code, database artifacts, visualizations, and documentation are ready for deployment."*
