import logging

import psycopg2
import os

from fastapi import HTTPException

from server.utils.user_service import initialize_db


class ProjectManager:

    is_deleted_condition = "AND is_deleted = false"

    def _create_table(self):
        initialize_db()
        conn = psycopg2.connect(os.getenv("POSTGRES_SERVER"))

        try:

            cursor = conn.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS projects (
                            id SERIAL PRIMARY KEY,
                            directory TEXT UNIQUE,
                            is_default BOOLEAN DEFAULT FALSE, 
                            project_name TEXT,
                            repo_name TEXT, 
                            branch_name TEXT,
                            user_id VARCHAR(255) NOT NULL,
                            commit_id VARCHAR(255), 
                            status VARCHAR(255) DEFAULT 'created',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE,
                            CHECK (status IN ('created', 'ready', 'error'))
                            );""")
            conn.commit()
        except psycopg2.Error as e:
            print("An error occurred: 1", e)
        finally:
            conn.close()

    def register_project(self, directory, project_name, repo_name, branch_name, user_id, commit_id, default: bool,
                         project_id=None):
        try:
            conn = psycopg2.connect(os.getenv("POSTGRES_SERVER"))
            cursor = conn.cursor()
            message = ""
            if project_id:
                cursor.execute('''
                    UPDATE projects
                    SET commit_id = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND user_id = %s
                    RETURNING id
                ''', (commit_id, project_id, user_id))
                message = f"Project '{project_id}' updated successfully."
            else:
                cursor.execute('''
                    INSERT INTO projects (directory, project_name, repo_name, branch_name, user_id, commit_id, is_default)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (directory, project_name, repo_name, branch_name, user_id, commit_id, default))
                message = f"Project '{project_name}' registered successfully."
            conn.commit()
            project_id = cursor.fetchone()[0]
            print(message)

        except psycopg2.Error as e:
            print("An error occurred:", e)
        finally:
            if conn:
                conn.close()
        return project_id

    def list_projects(self):
        project_list = []
        try:
            conn = psycopg2.connect(os.getenv("POSTGRES_SERVER"))
            cursor = conn.cursor()
            cursor.execute(f"SELECT id, directory, is_default FROM projects {self.is_deleted_condition}")
            projects = cursor.fetchall()
            for project in projects:
                project_dict = {
                    "id": project[0],
                    "directory": project[1],
                    "active": True if project[2] else False,
                }
                # Append the dictionary to the list
                project_list.append(project_dict)
        except psycopg2.Error as e:
            print("An error occurred: 3", e)
        finally:
            conn.close()
        return project_list

    def update_project_status(self, project_id, status):
        conn = psycopg2.connect(os.getenv("POSTGRES_SERVER"))
        try:
            cursor = conn.cursor()
            # Update project timestamp and status
            cursor.execute(
                "UPDATE projects SET updated_at = CURRENT_TIMESTAMP,"
                " status = %s WHERE id = %s",
                (status.value, project_id),
            )

            conn.commit()
            print(
                f"Project with ID {project_id} has now been updated with"
                f" status {status}."
            )
        except psycopg2.Error as e:
            print("An error occurred: 4", e)
        finally:
            conn.close()

    def get_active_project(self):
        try:
            conn = psycopg2.connect(os.getenv("POSTGRES_SERVER"))
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT id, directory FROM projects WHERE is_default = true {self.is_deleted_condition}"
            )
            project = cursor.fetchone()
            if project:
                return project[0]
            else:
                return None
        except psycopg2.Error as e:
            print("An error occurred: 5", e)
        finally:
            conn.close()

    def get_active_dir(self):
        global conn
        try:
            conn = psycopg2.connect(os.getenv("POSTGRES_SERVER"))

            cursor = conn.cursor()
            cursor.execute(
                f"SELECT id, directory FROM projects WHERE is_default = true  {self.is_deleted_condition}"
            )
            project = cursor.fetchone()
            if project:
                return project[1]
            else:
                return None
        except psycopg2.Error as e:
            print("An error occurred: 10", e)
        finally:
            conn.close()

    def get_project_from_db(self, project_name, user_id):
        try:
            conn = psycopg2.connect(os.getenv("POSTGRES_SERVER"))
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT project_name, directory, id, commit_id, status, is_deleted
                FROM projects 
                WHERE project_name = %s AND user_id = %s
            """,
                           (project_name, user_id),
                           )

            project = cursor.fetchone()
            if project:
                return project
            else:
                return None

        except psycopg2.Error as e:
            print("An error occurred:", e)

        finally:
            if "conn" in locals() and conn:
                conn.close()

    def get_project_from_db_by_id(self, project_id):
        try:
            conn = psycopg2.connect(os.getenv("POSTGRES_SERVER"))
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT project_name, directory, id 
                FROM projects 
                WHERE id = %s 
                {self.is_deleted_condition}
            """,
                (project_id,),
            )

            project = cursor.fetchone()
            if project:
                return project
            else:
                return None

        except psycopg2.Error as e:
            print("An error occurred:", e)

        finally:
            if "conn" in locals() and conn:
                conn.close()

    def get_project_reponame_from_db(self, project_id):
        try:
            conn = psycopg2.connect(os.getenv("POSTGRES_SERVER"))
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT project_name, directory, id 
                FROM projects 
                WHERE id = %s 
                {self.is_deleted_condition}
            """,
                (project_id,),
            )

            project = cursor.fetchone()
            if project:
                return project
            else:
                return None

        except psycopg2.Error as e:
            print("An error occurred:", e)

        finally:
            if "conn" in locals() and conn:
                conn.close()

    def get_project_repo_details_from_db(self, project_id, user_id):
        try:
            conn = psycopg2.connect(os.getenv("POSTGRES_SERVER"))
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT project_name, directory, id, repo_name, branch_name
                FROM projects 
                WHERE id = %s and user_id = %s 
                {self.is_deleted_condition}
            """,
                (project_id, user_id),
            )

            project = cursor.fetchone()
            if project:
                return project
            else:
                return None

        except psycopg2.Error as e:
            print("An error occurred:", e)

        finally:
            if "conn" in locals() and conn:
                conn.close()

    def get_repo_and_branch_name(self, project_id):
        conn = None
        try:
            conn = psycopg2.connect(os.getenv("POSTGRES_SERVER"))
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT repo_name, branch_name
                FROM projects 
                WHERE id = %s 
                {self.is_deleted_condition}
            """, (project_id,))

            result = cursor.fetchone()
            if result:
                return result
            else:
                return None

        except psycopg2.Error as e:
            print("An error occurred:", e)

        finally:
            conn.close()

    def get_project_from_db_by_id_and_user_id(self, project_id, user_id):
        try:
            conn = psycopg2.connect(os.getenv("POSTGRES_SERVER"))
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT project_name, directory, id 
                FROM projects 
                WHERE id = %s and user_id = %s 
                {self.is_deleted_condition}
            """,
                (project_id, user_id),
            )

            project = cursor.fetchone()
            if project:
                return project
            else:
                return None

        except psycopg2.Error as e:
            print("An error occurred:", e)

        finally:
            if "conn" in locals() and conn:
                conn.close()

    def get_parsed_project_branches(self, repo_name, user_id, default):
        try:
            conn = psycopg2.connect(os.getenv("POSTGRES_SERVER"))

            cursor = conn.cursor()

            # Build the base query
            query = (
                "SELECT id, branch_name, repo_name, updated_at, is_default,"
                f" status FROM projects WHERE user_id = %s {self.is_deleted_condition}"
            )
            params = [user_id]

            # Add conditions based on the parameters
            if default is not None:
                query += " AND is_default = %s"
                params.append(default)

            if repo_name is not None:
                query += " AND repo_name = %s"
                params.append(repo_name)
            cursor.execute(query, tuple(params))

            project = cursor.fetchall()
            return project

        except psycopg2.Error as e:
            print("An error occurred: 12", e)

        finally:
            if "conn" in locals() and conn:
                conn.close()

    def delete_project(self, project_id: int, user_id: str):
        conn = psycopg2.connect(os.getenv("POSTGRES_SERVER"))
        try:
            cursor = conn.cursor()
            query = """
                UPDATE projects
                SET is_deleted = true, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND user_id = %s AND is_deleted = false;
            """
            cursor.execute(query, (project_id, user_id))
            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="No matching project found or project is already deleted."
                )
            else:
                logging.info("Project deleted successfully.")
            conn.commit()
        except psycopg2.Error as e:
            HTTPException(
                status_code=400,
                detail="An error occurred while restoring the project"
            )
        finally:
            conn.close()

    def restore_project(self, project_id: int, user_id: str):
        try:
            conn = psycopg2.connect(os.getenv("POSTGRES_SERVER"))
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE projects
                SET is_deleted = false
                WHERE id = %s AND user_id = %s AND is_deleted = true
                RETURNING id
            """, (project_id, user_id))
            result = cursor.fetchone()
            conn.commit()
            if result:
                return f"Project with ID {result[0]} restored successfully."
            else:
                return "Project not found or already restored."
        except psycopg2.Error as e:
            print(f"An error occurred: {e}")
            return "Error occurred during restoration."
        finally:
            conn.close()

    def restore_all_project(self, repo_name: str, user_id: str):
        try:
            conn = psycopg2.connect(os.getenv("POSTGRES_SERVER"))
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE projects
                SET is_deleted = false
                WHERE repo_name = %s AND user_id = %s AND is_deleted = true
                RETURNING id
            """, (repo_name, user_id))
            result = cursor.fetchall()
            conn.commit()
            if result:
                print()
                return f"Project with repo_name {repo_name} restored successfully."
            else:
                return "Project not found or already restored."
        except psycopg2.Error as e:
            print(f"An error occurred: {e}")
            return "Error occurred during restoration."
        finally:
            conn.close()

    def delete_all_project_by_repo_name(self, repo_name: str, user_id: str):
        try:
            conn = psycopg2.connect(os.getenv("POSTGRES_SERVER"))
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE projects
                SET is_deleted = true
                WHERE repo_name = %s AND user_id = %s AND is_deleted = false
                RETURNING id
            """, (repo_name, user_id))
            result = cursor.fetchall()
            conn.commit()
            if result:
                print()
                return f"Projects with repo_name {repo_name} deleted successfully."
            else:
                return "Project not found or already restored."
        except psycopg2.Error as e:
            print(f"An error occurred: {e}")
            return "Error occurred during restoration."
        finally:
            conn.close()