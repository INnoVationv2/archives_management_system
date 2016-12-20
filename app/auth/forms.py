from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from ..models import User
from flask import flash
from re import match


class LoginForm(Form):
    email = StringField('登录邮箱', validators=[Required(), Length(1, 64)])
    password = PasswordField('密码', validators=[Required()])
    remember_me = BooleanField('保持登录')
    submit = SubmitField('登录')


class RegistrationForm(Form):
    email = StringField('邮箱', validators=[Required(), Length(1, 64)])
    username = StringField('用户名', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          '支持英文和字母下划线.')])
    password = PasswordField('密码', validators=[
        Required()])
    name = StringField('真实姓名', validators=[
        Required(), Length(1, 20)])
    submit = SubmitField('立即注册')

    def validate_email(self, field):
        if not match('[-_\w\.]{0,64}@([-\w]{1,63}\.)*[-\w]{1,63}', field.data):
            flash('邮箱地址格式错误,请重试')
        if User.query.filter_by(email=field.data).first():
            flash('邮箱已被注册.')

    def validate_name(self, field):
        if not match('^[a-zA-Z\u4e00-\u9fa5]*$', field.data):
            flash('真实姓名只能输入英文和中文.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            flash('用户名已被注册.')
        if not match('^[A-Za-z][A-Za-z0-9_.]*$', field.data):
            flash('用户名只支持英文和字母下划线.')


class PasswordResetRequestForm(Form):
    email = StringField('邮箱', validators=[Required(), Length(1, 64),
                                          Email()], )
    submit = SubmitField('提交')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            flash('邮箱不存在,请重新确认')


class PasswordChangeForm(Form):
    email = StringField('邮箱', validators=[Required(), Length(1, 64),
                                          Email()])
    password = PasswordField('密码', validators=[
        Required(), EqualTo('password2', message='两次密码不一致.')])
    password2 = PasswordField('确认密码', validators=[Required()])
    submit = SubmitField('修改')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            flash('邮箱不存在,请重新确认')


class ChangePasswordForm(Form):
    old_password = PasswordField('旧密码', validators=[Required()])
    password = PasswordField('新密码', validators=[
        Required(), EqualTo('password2', message='两次密码不一致.')])
    password2 = PasswordField('确认密码', validators=[Required()])
    submit = SubmitField('修改')


class ChangeEmailForm(Form):
    email = StringField('新邮箱地址', validators=[Required(), Length(1, 64),
                                             Email()])
    password = PasswordField('密码', validators=[Required()])
    submit = SubmitField('修改')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            flash('此邮箱已经注册.')
