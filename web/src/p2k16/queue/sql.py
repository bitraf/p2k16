
def set_processed(con, message_id: int):
    c = con.cursor()
    c.execute("UPDATE q_message SET processed_at=CURRENT_TIMESTAMP WHERE id=%s", [message_id])
    c.close()
