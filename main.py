from flask import Flask, jsonify, request
import mysql.connector
import uuid
#لسه محتاج اعمل لينك ب mysql server 
app = Flask()

db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "",
}


def get_db_connection():
    return mysql.connector.connect(**db_config)

# 1. REQUESTS ENDPOINTS

@app.route("/api/requests", methods=["GET"])
def get_requests():
    status = request.args.get("status")
    urgency = request.args.get("urgency")

    query = "SELECT * FROM Requests WHERE 1=1"
    params = []

    if status:
        query += " AND status = %s"
        params.append(status)
    if urgency:
        query += " AND urgency = %s"
        params.append(urgency)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, tuple(params))
    requests_list = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(requests_list), 200


@app.route("/api/requests", methods=["POST"])
def create_request():
    """Create a new item request for an organization."""
    data = request.get_json()
    request_id = str(uuid.uuid4())

    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO Requests (id, organization_id, category_id, item_name, quantity_needed, urgency)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    try:
        cursor.execute(
            query,
            (
                request_id,
                data["organization_id"],
                data["category_id"],
                data["item_name"],
                data["quantity_needed"],
                data["urgency"],
            ),
        )
        conn.commit()
        return (
            jsonify(
                {"id": request_id, "message": "Request created successfully"}
            ),
            201,
        )
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


@app.route("/api/requests/<request_id>", methods=["PATCH"])
def update_request_status(request_id):
    """Update request status (e.g., 'fulfilled' or 'cancelled')."""
    data = request.get_json()
    new_status = data.get("status")

    if new_status not in ["open", "fulfilled", "cancelled"]:
        return jsonify({"error": "Invalid status value"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Requests SET status = %s WHERE id = %s", (new_status, request_id)
    )
    conn.commit()
    affected_rows = cursor.rowcount
    cursor.close()
    conn.close()

    if affected_rows == 0:
        return jsonify({"error": "Request not found"}), 404

    return (
        jsonify(
            {
                "id": request_id,
                "status": new_status,
                "message": "Status updated successfully",
            }
        ),
        200,
    )

# 2. INSPECTIONS ENDPOINTS


@app.route("/api/inspections", methods=["POST"])
def create_inspection():
    """Logs an inspection and automatically syncs the associated donation's status in a transaction."""
    data = request.get_json()
    inspection_id = str(uuid.uuid4())
    result = data.get("result")  # 'approved', 'rejected', 'needs_maintenance'

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Step 1: Insert inspection log
        query_inspection = """
            INSERT INTO Inspections (id, donation_id, inspector_id, result, notes)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(
            query_inspection,
            (
                inspection_id,
                data["donation_id"],
                data["inspector_id"],
                result,
                data.get("notes"),
            ),
        )

        # Step 2: Map inspection result to Donation status and update
        donation_status = "approved" if result == "approved" else "rejected"
        cursor.execute(
            "UPDATE Donations SET status = %s WHERE id = %s",
            (donation_status, data["donation_id"]),
        )

        conn.commit()
        return (
            jsonify(
                {
                    "id": inspection_id,
                    "donation_status": donation_status,
                    "message": "Inspection recorded and donation status updated",
                }
            ),
            201,
        )

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


@app.route("/api/inspections/donation/<donation_id>", methods=["GET"])
def get_inspections_by_donation(donation_id):
    """Retrieve all inspection records for a specific donation."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM Inspections WHERE donation_id = %s ORDER BY inspected_at DESC",
        (donation_id,),
    )
    inspections = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(inspections), 200


# 3. DELIVERIES ENDPOINTS

@app.route("/api/deliveries", methods=["POST"])
def create_delivery():
    """Assign a courier and schedule a delivery for a confirmed match."""
    data = request.get_json()
    delivery_id = str(uuid.uuid4())

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO Deliveries (id, match_id, courier_name, pickup_date)
        VALUES (%s, %s, %s, %s)
    """
    try:
        cursor.execute(
            query,
            (
                delivery_id,
                data["match_id"],
                data.get("courier_name"),
                data.get("pickup_date"),
            ),
        )
        conn.commit()
        return (
            jsonify(
                {"id": delivery_id, "message": "Delivery created successfully"}
            ),
            201,
        )
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


@app.route("/api/deliveries/<delivery_id>", methods=["PATCH"])
def update_delivery_status(delivery_id):
    """Update shipment progress (assigned -> in_transit -> delivered/failed)."""
    data = request.get_json()
    status = data.get("status")
    delivery_date = data.get("delivery_date")  # Format: YYYY-MM-DD HH:MM:SS

    if status not in ["assigned", "in_transit", "delivered", "failed"]:
        return jsonify({"error": "Invalid delivery status"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    if status == "delivered" and delivery_date:
        query = "UPDATE Deliveries SET status = %s, delivery_date = %s WHERE id = %s"
        params = (status, delivery_date, delivery_id)
    else:
        query = "UPDATE Deliveries SET status = %s WHERE id = %s"
        params = (status, delivery_id)

    cursor.execute(query, params)
    conn.commit()
    affected_rows = cursor.rowcount
    cursor.close()
    conn.close()

    if affected_rows == 0:
        return jsonify({"error": "Delivery record not found"}), 404

    return (
        jsonify(
            {
                "id": delivery_id,
                "status": status,
                "message": "Delivery updated successfully",
            }
        ),
        200,
    )


if __name__ == "__main__":
    app.run(debug=True)