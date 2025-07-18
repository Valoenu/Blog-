from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


# WTForm for creating a blog post
class CreateBlogPostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post",)



class RegisterUserForm(FlaskForm):
    name = StringField('Your Name', validators=[DataRequired()])
    email = StringField('Add your email',validators=[DataRequired()])
    password = StringField('Add your password here', validators=[DataRequired()])
    submit = SubmitField('Register')

    

class LoginUserForm(FlaskForm):
    email = StringField('Add your email',validators=[DataRequired()])
    password = StringField('Add your password', validators=[DataRequired()])
    submit = SubmitField('Login')




class CommentPostForm(FlaskForm):
    text = CKEditorField('Write your comment...', validators=[DataRequired()])
    submit = SubmitField('post')
