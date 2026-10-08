Moti Kitchen - Unlimited Room

Features:
- Create a room and share the link.
- No participant limit: anyone with the link can join.
- Room stays open until Exit Room is pressed.
- Browser refresh/close and switching away do not close the room.
- Hosted on Render, so your laptop can be turned off after deployment; the public URL remains available through Render.
- Text and image messages.
- Any participant can delete a message for everyone.
- Back only clears the current user's visible chat and does not close the room.
- Exit Room closes the room for everyone.
- Kitchen background image included as static/moti-background.png.

Important:
The current app uses SQLite. Render's local filesystem is not a durable database across every restart/redeploy. For permanent room/message persistence across server restarts, use PostgreSQL or another persistent database.
