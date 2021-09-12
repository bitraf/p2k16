import sqlalchemy.orm


def insert(session: sqlalchemy.orm.Session, queue: str, entity_id: int):
    args = {'queue': queue, 'entity_id': entity_id, 'entity_id_str': str(entity_id)}

    session.execute("INSERT INTO q_message(created_at, queue, entity_id) "
                    "VALUES(CURRENT_TIMESTAMP, :queue, :entity_id);", args)

    session.execute(f"NOTIFY \"{queue}\", '{entity_id}';")
