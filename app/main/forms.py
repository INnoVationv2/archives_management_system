from flask_wtf import Form
from wtforms import StringField, SubmitField, SelectField, BooleanField
from wtforms import ValidationError
from wtforms.validators import Required, Length, Email, Regexp
from ..models import User
from flask_pagedown.fields import PageDownField


class SearchArchiveForm(Form):
    choices = [('Name', '姓名'), ('student_ID', '学号')]
    name = SelectField('', choices=choices)
    key_words = StringField('')
    search = SubmitField('搜索')


class SearchUserForm(Form):
    choices = [('Email', '邮箱'), ('Name', '姓名')]
    name = SelectField('', choices=choices)
    key_words = StringField('')
    search = SubmitField('搜索')
    return_confirm = SubmitField('确认返还')


class SearchApplicantForm(Form):
    choices = [('Name', '姓名')]
    name = SelectField('', choices=choices)
    key_words = StringField('')
    search = SubmitField('搜索')


class ArchiveInfoForm(Form):
    choices_sex = [('男', '男'), ('女', '女'), ('其他', '其他')]
    choices_grade = [('2012', '2012级'), ('2013', '2013级'), ('2014', '2014级')]
    choices_political_status = [('党员', '党员'), ('共青团员', '共青团员'), ('群众', '群众')]
    choices_nation = [('汉族', '汉族'), ('满族', '满族'), ('藏族', '藏族'), ('壮族', '壮族'), ('蒙古族', '蒙古族'), ('苗族', '苗族'),
                      ('维吾尔族', '维吾尔族'), ('羌族', '羌族')]

    name = StringField('姓名', validators=[Length(0, 64)])
    age = StringField('年龄', validators=[Length(0, 64)])
    birth = StringField('出生年月', validators=[Length(0, 64)])
    sex = SelectField('性别', choices=choices_sex)
    address = StringField('家庭住址', validators=[Length(0, 64)])
    academy = StringField('学院', validators=[Length(0, 64)])
    grade = SelectField('年级', choices=choices_grade)
    political_status = SelectField('政治面貌', choices=choices_political_status)
    ID_number = StringField('身份证号', validators=[Length(0, 64)])
    student_id = StringField('学号', validators=[Length(0, 64)])
    nation = SelectField('民族', choices=choices_nation)
    email = StringField('邮箱地址', validators=[Length(0, 64)])
    submit = SubmitField('确认提交')
    delete = SubmitField('删除')
    recovery = SubmitField('恢复')


class EditProfileForm(Form):
    name = StringField('姓名', validators=[Length(0, 64)])
    submit = SubmitField('提交')


class EditProfileAdminForm(Form):
    choices = [('1', '管理员'), ('2', '在校生'), ('3', '普通用户')]
    choices_confirm = [(True, '已验证'), (False, '未验证 ')]
    email = StringField('邮箱', validators=[Required(), Length(1, 64),
                                          Email()])
    username = StringField('用户名', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          '支持英文和字母下划线.')])
    confirmed = SelectField('账户激活状态', choices=choices_confirm)
    role = SelectField('权限', choices=choices)
    name = StringField('姓名', validators=[Length(0, 64)])
    submit = SubmitField('提交')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.user = user

    def validate_email(self, field):
        if field.data == self.user.username:
            return
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已被注册.')

    def validate_username(self, field):
        if field.data == self.user.username:
            return
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已被注册.')


class ComposeMailForm(Form):
    subject = StringField('主题')
    receiver = StringField('收件人')
    body = PageDownField('内容')
    send = SubmitField('发送')
    draft = SubmitField('存草稿')


class DeleteForm(Form):
    delete = SubmitField('删除')


class ArchiveApplyForm(Form):
    choices = [('1', '电子档案'), ('2', '实体档案')]
    student_id = StringField('学号')
    name = StringField('姓名')
    apply_type = SelectField('申请类型', choices=choices)
    reason = SelectField('申请理由')
    apply = SubmitField('申请')


class ArchiveApplyProcessForm(Form):
    reason = StringField('原因')
    admit = SubmitField('同意')
    forbid = SubmitField('拒绝')
    confirm = SubmitField('确认取走')
    return_confirm = SubmitField('确认归还')


class batch_managementForm(Form):
    choices_sex = [('', ''), ('男', '男'), ('女', '女')]
    choices_academy = [('', ''), ('计算机与信息技术学院', '计算机与信息技术学院'), ('音乐学院', '音乐学院')]
    choices_political_status = [('', ''), ('党员', '党员'), ('共青团员', '共青团员'), ('群众', '群众')]
    choices_status = [('', ''), ('0', '借出'), ('1', '在库')]
    sex = SelectField(choices=choices_sex)
    academy = SelectField(choices=choices_academy)
    political_status = SelectField(choices=choices_political_status)
    political_status_2 = SelectField(choices=choices_political_status)
    status = SelectField(choices=choices_status)
    status_2 = SelectField(choices=choices_status)
    grade = StringField('年级')
    submit = SubmitField('提交')
    alter = SubmitField('提交')
