"""
Access.py

Module for a login page

"""

from flask import Flask, render_template, flash, redirect, url_for, request
from flask import g, session, abort
from wtforms import Form, validators, StringField, SelectField, TextAreaField
from wtforms import IntegerField, PasswordField, SelectMultipleField, widgets
import datetime as dt
import os
import pandas as pd
from functools import wraps
from passlib.hash import sha256_crypt


# -------------------------------- Forms ------------------------------------ #
#          USERS, Change Password, MultiCheckboxField, AccessForm             #
# --------------------------------------------------------------------------- #

password_message = ("Password must be mimimum 8 characters and contain only" +
                    " uppercase letters, lowercase letters and numbers")


class Users_Form(Form):
    username = StringField('Username', [validators.Length(min=4, max=25)])
    password = PasswordField('Password',
                             [validators.Regexp('^([a-zA-Z0-9]{8,})$',
                                                message=password_message)])


class ChangePwdForm(Form):
    current = PasswordField('Current password', [validators.DataRequired()])
    new = PasswordField('New password',
                        [validators.Regexp('^([a-zA-Z0-9]{8,})$',
                                           message=password_message)])
    confirm = PasswordField('Confirm new password',
                            [validators.EqualTo('new',
                                                message='Passwords do no match')])


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class AccessForm(Form):
    username = StringField('Username')
    Role = SelectField(u'*Role', [validators.NoneOf(('blank'),
                       message='Please select')])
    # Note levels of editor?


def table_list(tableClass, col, conn):
    DF = pd.read_sql_query("SELECT * FROM roles ;", conn)
    list = [('blank', '--Please select--')]
    for element in DF[col]:
        list.append((element, element))
    return list

def yesno_list():
    """generate yes no list for forms
    """
    list = []
    list.append(('blank', '--Please select--'))
    list.append(('Yes', 'Yes'))
    list.append(('No', 'No'))
    return list


#def option_list(col_name, conn):
#    """Create list of options on forms
#    args:
#        col_name(str): e.g. Area or country (must match db col name)
#        conn: database connection
#    returns: list
#    """
#    # Columns: area and regions
#    list = []
#    list.append(('blank', '--Please select--'))
#    if col_name == 'country':
#        # find unique values
#        df = pd.read_sql_query("select " + col_name +
#                               ", Area from  'VolcDB1'; ", conn)
#    else:
#        df = pd.read_sql_query("select " + col_name + " from  'VolcDB1'; ",
#                               conn)
#    existing = df.drop_duplicates()
#    # get rid of any missing values
#    existing = existing.dropna()
#    # Order by Region
#    existing = existing.sort_values('Area')
#    existing = existing.reset_index(drop=True)
#    # Remove incorrect values
#    existing = existing[~existing.Area.str.contains('0')]
#    # make a list
#    if col_name == 'country':
#        # there is one crazy volcano ?!?! remove it dropdown!!
#        existing = existing[~existing.country.str.contains('161.08')]
#        for element in existing.iterrows():
#            list.append((element[1][0], str(element[1][0]) +
#                         '(' + element[1][1] + ')'))
#    else:
#        for element in existing.iterrows():
#            list.append((element[1][0], element[1][0]))
#
#    # add the option of other
#    if list[-1][0] == '0':
#        list[-1] = (('other', 'other --Please Specify--'))
#    else:
#        list.append(('other', 'other --Please Specify--'))
#        # Find all current options
#    return list
#
#
# ------------------------- is logged in wrappers --------------------------- #
#                        logged_in as user editor admin                       #
# --------------------------------------------------------------------------- #

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorised, please login', 'danger')
            return redirect(url_for('main_bp.index'))
    return wrap


# Check if user is logged in as a trainer/admin
def is_logged_in_as_editor(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session and (session['usertype'] == 'Collaborators'
                                       or session['usertype'] == 'Admins'):
            return f(*args, **kwargs)
        else:
            flash('Unauthorised, please login as a editor/admin', 'danger')
            return redirect(url_for('main_bp.index'))
    return wrap


# Check if user is logged in as admin
def is_logged_in_as_admin(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session and session['usertype'] == 'Admins':
            return f(*args, **kwargs)
        else:
            flash('Unauthorised, please login as admin', 'danger')
            return redirect(url_for('main_bp.index'))
    return wrap

# ------------------------- User Access and Login --------------------------- #
#                         Add, Delete, Edit role, login                       #
# --------------------------------------------------------------------------- #


def InsertUser(username, password, conn):
    """InsertUser
    Description:
        Inserts user into database and hashes password
    Args:
        username (str): username e.g jsmith
        password (str): password must be more than 8 characters
    Returns:
        commits user to database as registered user
    """
    # create a cursor
    cur = conn.cursor()
    # Insert user into table
    cur.execute("INSERT INTO users (username,password) VALUES (?,?)",
                (username, password))
    # All new users automatically become a registerd user
    AssignRole(username, 'Registered_Users', conn)
    conn.commit()


def OptionalInfo(username, conn, affiliation=None,
                 email=None, request=None, consent=None):
    """OptionalInfo
    Description:
        Inserts user into database and hashes password
    Args:
        username (str): username e.g jsmith
        password (str): password must be more than 8 characters
    Kargs:
        affiliation (str): Institute affiliation (optional)
        email (str): optional Email address (required only for Collaborators)
        request collaborator (str): optional 'Y' or 'N'
        consent_regional_map_anon (str): consent to anonomous data added to
                                         regional users map? defaults to None
    Returns:
        commits user to database as registered user
    """
    id = None
    cur.execute("INSERT INTO users (affiliation,email) VALUES (?)",
                (str(affiliation), str(email)))
    conn.commit()


def DeleteUser(username, conn):
    """DeleteUser
    Description:
        Delets user from database
    Args:
        username (str): username e.g jsmith
        conn (db connection): database connection to volcano.db
    Kargs:
        affiliation (str): Institute affiliation (optional)
        email (str): Email address (required only for Collaborators)
        request collaborator (str): 'Y' or 'N', defaults to 'N'
        consent_regional_map_anon (str): consent to anonomous data added to
                                         regional users map? defaults to 'N'
    Returns:
        commits user to database as registered user
    """
    cur = conn.cursor()
    sql = 'DELETE FROM users WHERE username=?'
    cur.execute(sql, (username,))
    conn.commit()


def AssignRole(username, role, conn):
    """AssignRole
    Description:
        Delets user from database
    Args:
        username (str): username e.g jsmith
        role (str): predefined role name
        conn (db connection): database connection to volcano.db
    Kargs:
        affiliation (str): Institute affiliation (optional)
        email (str): Email address (required only for Collaborators)
        request collaborator (str): 'Y' or 'N', defaults to 'N'
        consent_regional_map_anon (str): consent to anonomous data added to
                                         regional users map? defaults to 'N'
    Returns:
        commits user to database as registered user
    """
    if str(role) not in ['Registered_Users', 'Collaborators', 'Admins']:
        return print('Role must be one of: Registered_Users, Collaborators, Admins')
    cur = conn.cursor()
    sql = "SELECT * FROM  users WHERE username is '"+f"{str(username)}"+"';"
    user = pd.read_sql_query(sql, conn)
    sql = ("SELECT group_id FROM  users_roles WHERE id is '" +
           f"{str(user.id.values[0])}"+"';")
    exist_role = pd.read_sql_query(sql, conn)
    if not exist_role.empty:
        sql = 'DELETE from users_roles where id = ?'
        cur.execute(sql, (str(user.id.values[0]),))
    sql = "SELECT * FROM roles WHERE name is '"+f"{str(role)}"+"';"
    role = pd.read_sql_query(sql, conn)
    sql = 'INSERT into users_roles VALUES(?,?)'
    cur.execute(sql, (str(user.id.values[0]), str(role.group_id.values[0])))
    conn.commit()


def user_login(username, password_candidate, conn):
    user = pd.read_sql_query("SELECT * FROM  users WHERE username is '"
                             + str(username) + "';", conn)
    roles = pd.read_sql_query("SELECT * FROM  roles;", conn)
    if user.empty is False and str(username) != 'admin':
        password = user.password[0]
        # Compare passwords
        if sha256_crypt.verify(str(password_candidate), password):
            # Passed
            flash('You are now logged in', 'success')
            roleid = pd.read_sql_query("SELECT * FROM users_roles WHERE id " +
                                       "is " + str(user.id[0]) + ";", conn)
            role = pd.read_sql_query("SELECT * FROM roles WHERE group_id " +
                                     "is " + str(roleid.group_id[0]) + ";",
                                     conn)
            session['logged_in'] = True
            session['username'] = str(username)
            session['usertype'] = str(role.name[0])
            if session['usertype'] == 'Admins':
                flash('You have admin privileges', 'success')
        else:
            flash('Incorrect password', 'danger')

    elif user.empty is True and str(username) != 'admin':
        # Username not found:
        flash('Username ' + str(username) + ' not found', 'danger')
        return redirect(url_for('main_bp.login'))
    if str(username) == 'admin':
        password = 'password'
        if password_candidate == password:
            # Passed
            session['logged_in'] = True
            session['username'] = 'admin'
            session['usertype'] = 'Admins'
            flash('You are now logged in as admin', 'success')
            return redirect(url_for('main_bp.login'))
        else:
            flash('Incorrect password', 'danger')
            return redirect(url_for('main_bp.login'))
    return
