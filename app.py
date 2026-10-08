from flask import Flask, render_template, request, jsonify, abort, session, redirect, url_for
from datetime import datetime
from werkzeug.utils import secure_filename
import os, uuid, sqlite3

app=Flask(__name__)
app.secret_key=os.environ.get("SECRET_KEY","change-this-secret-key")
BASE=os.path.dirname(os.path.abspath(__file__))
UPLOAD=os.path.join(BASE,"static","uploads"); os.makedirs(UPLOAD,exist_ok=True)
DB=os.path.join(BASE,"database.db")

def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init():
    c=db()
    c.execute("CREATE TABLE IF NOT EXISTS rooms(room_id TEXT PRIMARY KEY,closed INTEGER DEFAULT 0,created_at TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS users(room_id TEXT,user_id TEXT,username TEXT,category TEXT,cleared_at TEXT,PRIMARY KEY(room_id,user_id))")
    c.execute("CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT,room_id TEXT,user_id TEXT,username TEXT,kind TEXT,content TEXT,created_at TEXT)")
    c.commit(); c.close()
init()

CATS=["Dal Chawal","Chicken Fry","Biryani","Noodles","Fast Food","Sabzi","Breakfast","Desserts","Drinks","Others"]

def valid(rid):
    c=db(); x=c.execute("SELECT closed FROM rooms WHERE room_id=?",(rid,)).fetchone(); c.close()
    return x is not None and x["closed"]==0

@app.route("/")
def home(): return redirect(url_for("create"))

@app.route("/create")
def create():
    rid=uuid.uuid4().hex
    c=db(); c.execute("INSERT INTO rooms VALUES(?,?,?)",(rid,0,datetime.utcnow().isoformat())); c.commit(); c.close()
    return render_template("create.html",room_id=rid)

@app.route("/room/<rid>")
def room(rid):
    if not valid(rid): abort(404)
    return render_template("login.html",room_id=rid,categories=CATS)

@app.post("/join/<rid>")
def join(rid):
    if not valid(rid): return jsonify(error="closed"),404
    name=(request.form.get("username") or "").strip()
    cat=request.form.get("category","Others")
    if not name: return jsonify(error="username required"),400
    if cat not in CATS: cat="Others"
    c=db()
    # No participant limit: anyone with the room link can join.
    uid=uuid.uuid4().hex
    c.execute("INSERT INTO users VALUES(?,?,?,?,?)",(rid,uid,name,cat,"")); c.commit(); c.close()
    session.update(room_id=rid,user_id=uid,username=name)
    return redirect(url_for("chat",rid=rid))

@app.route("/chat/<rid>")
def chat(rid):
    if not valid(rid) or session.get("room_id")!=rid: abort(404)
    return render_template("chat.html",room_id=rid,username=session["username"])

@app.get("/api/messages/<rid>")
def msgs(rid):
    if not valid(rid) or session.get("room_id")!=rid: return jsonify(error="closed"),404
    c=db(); u=c.execute("SELECT cleared_at FROM users WHERE room_id=? AND user_id=?",(rid,session["user_id"])).fetchone()
    rows=c.execute("SELECT id,user_id,username,kind,content,created_at FROM messages WHERE room_id=? AND created_at>? ORDER BY id",(rid,u["cleared_at"] or "")).fetchall()
    c.close(); return jsonify(messages=[dict(x) for x in rows])

@app.post("/api/send/<rid>")
def send(rid):
    if not valid(rid) or session.get("room_id")!=rid: return jsonify(error="closed"),404
    text=(request.form.get("text") or "").strip()
    if not text:return jsonify(error="empty"),400
    c=db(); c.execute("INSERT INTO messages(room_id,user_id,username,kind,content,created_at) VALUES(?,?,?,?,?,?)",(rid,session["user_id"],session["username"],"text",text,datetime.utcnow().isoformat())); c.commit(); c.close()
    return jsonify(ok=True)

@app.post("/api/send-image/<rid>")
def image(rid):
    if not valid(rid) or session.get("room_id")!=rid:return jsonify(error="closed"),404
    f=request.files.get("image")
    if not f:return jsonify(error="image required"),400
    ext=os.path.splitext(secure_filename(f.filename))[1].lower()
    if ext not in [".jpg",".jpeg",".png",".gif",".webp"]:return jsonify(error="unsupported image"),400
    name=uuid.uuid4().hex+ext; f.save(os.path.join(UPLOAD,name))
    c=db(); c.execute("INSERT INTO messages(room_id,user_id,username,kind,content,created_at) VALUES(?,?,?,?,?,?)",(rid,session["user_id"],session["username"],"image","/static/uploads/"+name,datetime.utcnow().isoformat())); c.commit(); c.close()
    return jsonify(ok=True)

@app.post("/api/delete/<rid>/<int:mid>")
def delete(rid,mid):
    if not valid(rid) or session.get("room_id")!=rid:return jsonify(error="closed"),404
    c=db(); c.execute("DELETE FROM messages WHERE id=? AND room_id=?",(mid,rid)); c.commit(); c.close(); return jsonify(ok=True)

@app.post("/api/back/<rid>")
def back(rid):
    if not valid(rid) or session.get("room_id")!=rid:return jsonify(error="closed"),404
    c=db(); c.execute("UPDATE users SET cleared_at=? WHERE room_id=? AND user_id=?",(datetime.utcnow().isoformat(),rid,session["user_id"])); c.commit(); c.close(); return jsonify(ok=True)

@app.post("/api/exit/<rid>")
def exit_room(rid):
    if session.get("room_id")!=rid:return jsonify(error="closed"),404
    c=db(); c.execute("UPDATE rooms SET closed=1 WHERE room_id=?",(rid,)); c.commit(); c.close(); session.clear()
    return jsonify(ok=True)

@app.errorhandler(404)
def nf(e): return render_template("expired.html"),404

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)),debug=True)
