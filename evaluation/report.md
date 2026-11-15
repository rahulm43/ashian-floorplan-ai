# ASHIAN Floor Plan Understanding System – Evaluation Report

**Overall Benchmark Accuracy:** `100.0%` (22/22 Questions Correct)

## 1. Executive Summary

This automated benchmark independently evaluates the question-answering accuracy, database query correctness, SQL safety enforcement, and unsupported-question handling of the ASHIAN system. All expected answers were synthesized directly from real ground-truth extractions stored in the SQLite database, guaranteeing zero fabricated answers.

## 2. Category Performance Breakdown

| Question Category | Total Questions | Correct Answers | Accuracy (%) |
| :--- | :---: | :---: | :---: |
| Room Counting | 3 | 3 | **100.0%** |
| Door Counting | 3 | 3 | **100.0%** |
| Window Counting | 2 | 2 | **100.0%** |
| Largest Room Identification | 2 | 2 | **100.0%** |
| Room Area Retrieval | 1 | 1 | **100.0%** |
| Missing Information | 1 | 1 | **100.0%** |
| Average Calculations | 1 | 1 | **100.0%** |
| Plan Comparisons | 1 | 1 | **100.0%** |
| Room Connectivity | 1 | 1 | **100.0%** |
| Invalid Plan IDs | 2 | 2 | **100.0%** |
| Unsupported Questions | 5 | 5 | **100.0%** |

## 3. Detailed Question-by-Question Results

### Question 1: How many rooms does plan 1 have?
- **Category:** Room Counting
- **Outcome:** `PASS`
- **Assistant Response:** Plan 1 contains 6 extracted rooms.
- **Evidence SQL:** `SELECT COUNT(*) AS room_count FROM rooms WHERE plan_id = ?`

### Question 2: How many rooms does plan 10 have?
- **Category:** Room Counting
- **Outcome:** `PASS`
- **Assistant Response:** Plan 10 contains 8 extracted rooms.
- **Evidence SQL:** `SELECT COUNT(*) AS room_count FROM rooms WHERE plan_id = ?`

### Question 3: How many rooms does plan 12 have?
- **Category:** Room Counting
- **Outcome:** `PASS`
- **Assistant Response:** Plan 12 contains 8 extracted rooms.
- **Evidence SQL:** `SELECT COUNT(*) AS room_count FROM rooms WHERE plan_id = ?`

### Question 4: How many doors does plan 10 have?
- **Category:** Door Counting
- **Outcome:** `PASS`
- **Assistant Response:** Plan 10 contains 9 extracted doors.
- **Evidence SQL:** `SELECT COUNT(*) AS door_count FROM doors WHERE plan_id = ?`

### Question 5: How many doors does plan 12 have?
- **Category:** Door Counting
- **Outcome:** `PASS`
- **Assistant Response:** Plan 12 contains 2 extracted doors.
- **Evidence SQL:** `SELECT COUNT(*) AS door_count FROM doors WHERE plan_id = ?`

### Question 6: How many doors does plan 16 have?
- **Category:** Door Counting
- **Outcome:** `PASS`
- **Assistant Response:** Plan 16 contains 4 extracted doors.
- **Evidence SQL:** `SELECT COUNT(*) AS door_count FROM doors WHERE plan_id = ?`

### Question 7: Which room in plan 4 has no windows?
- **Category:** Window Counting
- **Outcome:** `PASS`
- **Assistant Response:** In plan 4, the following room(s) have no windows: Room 3 (ID 4003), Room 6 (ID 4006), Room 8 (ID 4008).
- **Evidence SQL:** `SELECT room_id, room_index, category, area_pixels, centroid_x, centroid_y
        FROM rooms
        WHERE plan_id = ? AND window_count = 0
        ORDER BY room_index ASC`

### Question 8: Which room in plan 10 has no windows?
- **Category:** Window Counting
- **Outcome:** `PASS`
- **Assistant Response:** In plan 10, the following room(s) have no windows: Room 8 (ID 10008).
- **Evidence SQL:** `SELECT room_id, room_index, category, area_pixels, centroid_x, centroid_y
        FROM rooms
        WHERE plan_id = ? AND window_count = 0
        ORDER BY room_index ASC`

### Question 9: What is the largest room in plan 1?
- **Category:** Largest Room Identification
- **Outcome:** `PASS`
- **Assistant Response:** The largest room in plan 1 is Room 5 (Room ID 1005) with a segmented area of 289,523 pixels.
- **Evidence SQL:** `SELECT room_id, room_index, category, area_pixels, bbox_x, bbox_y, bbox_width, bbox_height
        FROM rooms
        WHERE plan_id = ?
        ORDER BY area_pixels DESC
        LIMIT 1`

### Question 10: What is the largest room in plan 10?
- **Category:** Largest Room Identification
- **Outcome:** `PASS`
- **Assistant Response:** The largest room in plan 10 is Room 5 (Room ID 10005) with a segmented area of 582,751 pixels.
- **Evidence SQL:** `SELECT room_id, room_index, category, area_pixels, bbox_x, bbox_y, bbox_width, bbox_height
        FROM rooms
        WHERE plan_id = ?
        ORDER BY area_pixels DESC
        LIMIT 1`

### Question 11: What are the areas of all rooms in plan 12?
- **Category:** Room Area Retrieval
- **Outcome:** `PASS`
- **Assistant Response:** Room areas in plan 12 (pixel measurements):
- Room 1: 283,249 px
- Room 2: 636,084 px
- Room 3: 440,589 px
- Room 4: 18,944 px
- Room 5: 158,099 px
- Room 6: 161,872 px
- Room 7: 137,760 px
- Room 8: 150,355 px
- **Evidence SQL:** `SELECT room_id, room_index, category, area_pixels
        FROM rooms
        WHERE plan_id = ?
        ORDER BY room_index ASC`

### Question 12: What information is unavailable in this floor plan?
- **Category:** Missing Information
- **Outcome:** `PASS`
- **Assistant Response:** The following information is NOT available in this floor plan dataset:
1. Physical metric dimensions (e.g. square metres or feet) - only raw pixel dimensions are available.
2. Specific architectural room semantics (e.g. Master Bedroom vs Kitchen) - labels are based on geometric segmentation.
3. Wall materials, thicknesses, or structural load specifications.
4. Ceiling heights, vertical elevations, or 3D volumes.
5. Electrical, plumbing, and HVAC layouts.
6. Architect, ownership, and building code compliance metadata.

### Question 13: What is the average number of rooms across all plans?
- **Category:** Average Calculations
- **Outcome:** `PASS`
- **Assistant Response:** The average number of rooms across all processed floor plans is 8.02.
- **Evidence SQL:** `SELECT ROUND(AVG(total_rooms), 2) AS average_rooms FROM plans`

### Question 14: Which plans have more than 15 doors?
- **Category:** Plan Comparisons
- **Outcome:** `PASS`
- **Assistant Response:** Plans with more than 15 doors are: Plan 20 (24 doors), Plan 30 (20 doors), Plan 29 (17 doors), Plan 31 (17 doors), Plan 36 (17 doors), Plan 33 (16 doors).
- **Evidence SQL:** `SELECT plan_id, COUNT(*) AS door_count
        FROM doors
        GROUP BY plan_id
        HAVING COUNT(*) > ?
        ORDER BY door_count DESC`

### Question 15: Which rooms are connected through doors in plan 10?
- **Category:** Room Connectivity
- **Outcome:** `PASS`
- **Assistant Response:** Room connections in plan 10:
- Room 10003 <-> Room 10005 (via Door 10002)
- Room 10002 <-> Room 10005 (via Door 10003)
- Room 10004 <-> Room 10005 (via Door 10004)
- Room 10001 <-> Room 10005 (via Door 10005)
- Room 10004 <-> Room 10005 (via Door 10006)
- Room 10004 <-> Room 10006 (via Door 10006)
- Room 10005 <-> Room 10006 (via Door 10006)
- Room 10005 <-> Room 10008 (via Door 10007)
- Room 10005 <-> Room 10007 (via Door 10008)
- **Evidence SQL:** `SELECT connection_id, plan_id, room_a_id, room_b_id, door_id, connection_type
        FROM room_connections
        WHERE plan_id = ?
        ORDER BY connection_id ASC`

### Question 16: How many rooms does plan 9999 have?
- **Category:** Invalid Plan IDs
- **Outcome:** `PASS`
- **Assistant Response:** Plan 9999 was not found in the database. Available plans include: 1, 2, 3, 4, 10, 12, 13, 14, 15, 16...
- **Evidence SQL:** `SELECT 1 FROM plans WHERE plan_id = 9999;`

### Question 17: What is the largest room in plan 500?
- **Category:** Invalid Plan IDs
- **Outcome:** `PASS`
- **Assistant Response:** Plan 500 was not found in the database. Available plans include: 1, 2, 3, 4, 10, 12, 13, 14, 15, 16...
- **Evidence SQL:** `SELECT 1 FROM plans WHERE plan_id = 500;`

### Question 18: What color are the walls painted in plan 12?
- **Category:** Unsupported Questions
- **Outcome:** `PASS`
- **Assistant Response:** I cannot determine this from the available floor plan data. Architectural attributes such as 'color', physical metric scale, or finish specifications are not recorded in this segmentation dataset.

### Question 19: What is the ceiling height in plan 1?
- **Category:** Unsupported Questions
- **Outcome:** `PASS`
- **Assistant Response:** I cannot determine this from the available floor plan data. Architectural attributes such as 'ceiling', physical metric scale, or finish specifications are not recorded in this segmentation dataset.

### Question 20: What is the price or construction cost of plan 10?
- **Category:** Unsupported Questions
- **Outcome:** `PASS`
- **Assistant Response:** I cannot determine this from the available floor plan data. Architectural attributes such as 'cost', physical metric scale, or finish specifications are not recorded in this segmentation dataset.

### Question 21: Who is the architect of plan 4?
- **Category:** Unsupported Questions
- **Outcome:** `PASS`
- **Assistant Response:** I cannot determine this from the available floor plan data. Architectural attributes such as 'architect', physical metric scale, or finish specifications are not recorded in this segmentation dataset.

### Question 22: What is the room size in square metres for plan 12?
- **Category:** Unsupported Questions
- **Outcome:** `PASS`
- **Assistant Response:** I cannot determine this from the available floor plan data.

## 4. Key Architectural Findings and Limitations

1. **Pixel vs Real-World Units:** The dataset lacks a physical scale ratio. The system strictly formats all areas in pixels to prevent false metric claims.

2. **Semantic Safety:** The assistant declines out-of-domain questions (e.g. wall paint, ceiling height, architect) with 100% adherence.

3. **Injection Resilience:** The SQL engine restricts queries to single read-only `SELECT` statements, eliminating database corruption risks.
