# ~ Import Date Library ~
from datetime import date

# ~ Import Flask Libraries ~
from flask import Flask, abort, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy

# ~ Import your own forms  ~ 
from forms import CreateBlogPostForm, LoginUserForm, RegisterUserForm, CommentForm

# ~ Import SQL Libraries ~ 
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text

# ~ Import other Libraries ~
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

# ~ Set Flask ~
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # ~ Set your own secret key ~ 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog-posts.db'
ckeditor = CKEditor(app)
Bootstrap5(app)

# ~ DATABASE PROCESS ~
class Base(DeclarativeBase):
    pass

database = SQLAlchemy(model_class=Base)
database.init_app(app)

# ~ CREATE TABLE PROCESS ~
class PostToBlog(database.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    author: Mapped[str] = mapped_column(String(250), nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    url_image: Mapped[str] = mapped_column(String(250), nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, database.ForeignKey('users.id'))  # ~ Create foreign key, users.id ~
    author = relationship('User', back_populates='posts')  # ~ Relationship to User table ~
    comments = relationship('CommentPost', back_populates='post_main')  # ~ Relationship to comments table ~


# ~ Use request.form.get to create User Registered Table (Use UserMixin) ~ 
class User(UserMixin, database.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True)
    password: Mapped[str] = mapped_column(String(150))
    posts = relationship('PostToBlog', back_populates='author')
    comments = relationship('CommentPost', back_populates='author_comment')


# ~ Create table to allow users leave a comment below our blog posts ~
class CommentPost(database.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    id_author: Mapped[int] = mapped_column(Integer, database.ForeignKey('users.id'))
    author_comment = relationship('User', back_populates='comments')
    post_id: Mapped[int] = mapped_column(Integer, database.ForeignKey("blog_posts.id"))
    post_main = relationship("PostToBlog", back_populates="comments")


# ~ Set your login manager ~
login_manager = LoginManager()
login_manager.init_app(app)

# ~ Creating user_loader process ~
@login_manager.user_loader 
def load_user(user_id):
    return database.get_or_404(User, user_id)


# ~ Write your own @admin_mode Decorator ~
def admin_mode(function):
    @wraps(function)
    def wrapper_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.id == 1:
            return function(*args, **kwargs)
        else:
            return abort(403)
    return wrapper_function


# ~ Home route ~
@app.route('/')
def home():
    outcome = database.session.execute(database.select(PostToBlog))
    blog_posts = outcome.scalars().all()
    return render_template("index.html", posts=blog_posts, user_authenticated=True, present_user=current_user)


# ~ Register Route ~
@app.route('/register', methods=["POST", "GET"])
def register():
    form = RegisterUserForm()
    if form.validate_on_submit():
        email = form.email.data
        outcome = database.session.execute(database.select(User).where(User.email == email))
        user = outcome.scalar()

        if user:
            flash('This email has already signed up, you can log in')
            return redirect(url_for('login'))

        salted_hash_password = generate_password_hash(
            form.password.data,
            method="pbkdf2:sha256",
            salt_length=15
        )

        user_new = User(
            name=form.name.data,
            email=form.email.data,
            password=salted_hash_password,
        )

        database.session.add(user_new)
        database.session.commit()
        login_user(user_new)
        return redirect(url_for('home'))

    return render_template("register.html", form=form, present_user=current_user)


# ~ Login Route ~
@app.route('/login', methods=["POST", "GET"])
def login():
    form = LoginUserForm()
    if form.validate_on_submit():
        password = form.password.data
        email = form.email.data

        outcome = database.session.execute(database.select(User).where(User.email == email))
        user = outcome.scalar()

        if not user:
            flash("That email does not exist.")
            return redirect(url_for('login'))

        if not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))

        login_user(user)
        return redirect(url_for('home'))

    return render_template("login.html", form=form, user_authenticated=True, present_user=current_user)


# ~ Logout Route ~
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


# ~ Show Blog Post and Comment ~
@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
@login_required
def blog_post_show(post_id):
    requested_post = database.get_or_404(PostToBlog, post_id)
    form_comment = CommentForm()

    if form_comment.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Login or register to comment')
            return redirect(url_for('login'))

        new_post_comment = CommentPost(
            text=form_comment.comment_text.data,
            author_comment=current_user,
            post_main=requested_post
        )
        database.session.add(new_post_comment)
        database.session.commit()

    return render_template("post.html", post=requested_post, user_authenticated=True, present_user=current_user, form=form_comment)


# ~ Add New Post (Admin Only) ~
@app.route("/new-blog-post", methods=["GET", "POST"])
@admin_mode
def add_new_post():
    form = CreateBlogPostForm()
    if form.validate_on_submit():
        new_post = PostToBlog(
            title=form.title.data,
            subtitle=form.subtitle.data,
            text=form.body.data,
            url_image=form.img_url.data,
            author=current_user.name,
            author_id=current_user.id,
            date=date.today().strftime("%B %d, %Y")
        )
        database.session.add(new_post)
        database.session.commit()
        return redirect(url_for("home"))
    return render_template("make-post.html", form=form, user_authenticated=True, present_user=current_user)


# ~ Edit Post (Admin Only) ~
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_mode
def edit_post(post_id):
    post = database.get_or_404(PostToBlog, post_id)
    edit_form = CreateBlogPostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.url_image,
        author=post.author,
        body=post.text
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.url_image = edit_form.img_url.data
        post.author = current_user.name
        post.text = edit_form.body.data
        database.session.commit()
        return redirect(url_for("blog_post_show", post_id=post.id))

    return render_template("make-post.html", form=edit_form, is_edit=True, user_authenticated=True, present_user=current_user)


# ~ Delete Post (Admin Only) ~
@app.route("/delete/<int:post_id>")
@admin_mode
def delete_post(post_id):
    delete_this_post = database.get_or_404(PostToBlog, post_id)
    database.session.delete(delete_this_post)
    database.session.commit()
    return redirect(url_for('home'))


# ~ About Page ~
@app.route("/about")
def about():
    return render_template("about.html", present_user=current_user)


# ~ Contact Page ~
@app.route("/contact")
def contact():
    return render_template("contact.html", present_user=current_user)


# ~ Gravatar Avatar for Comments ~
from flask_gravatar import Gravatar
avatars = Gravatar(
    app,
    size=100,
    rating='g',
    default='retro',
    force_default=False,
    force_lower=False,
    use_ssl=False,
    base_url=None
)


# ~ Create Database Tables ~
with app.app_context():
    database.create_all()


# ~ Run App ~
if __name__ == "__main__":
    app.run(debug=True, port=5002)
