""" oracle specific connection methods"""
import logging

LOGGER = logging.getLogger(__name__)


def connection_info(con):
    """get connection info from connected database"""
    conn_info = {'dbversion': "", 'sid': 0, 'instance_type': "rdbms",
                 'serial': 0, 'db_role': "", 'uname': "",
                 'iname': ""}
    _c = con.cursor()
    try:
        _c.execute("""select substr(i.version,0,instr(i.version,'.')-1),
          s.sid, s.serial#, p.value instance_type, i.instance_name
          , s.username
          from v$instance i, v$session s, v$parameter p
          where s.sid = (select sid from v$mystat where rownum = 1)
          and p.name = 'instance_type'""")

        _data = _c.fetchone()

        conn_info['dbversion'] = _data[0]
        conn_info['sid'] = _data[1]
        conn_info['serial'] = _data[2]
        conn_info['instance_type'] = _data[3]
        conn_info['iname'] = _data[4]
        conn_info['uname'] = _data[5]

    except con.DatabaseError as dberr:
        _error, = dberr.args

        if _error.code == 904:
            conn_info['dbversion'] = "pre9"
        elif _error.code == 942:
            LOGGER.critical(
                "Missing required privileges \n"
                "(grant create session, select any dictionary, oem_monitor)")
            raise
        else:
            print(_error.code)
            conn_info['dbversion'] = "unk"

    if conn_info['instance_type'] == "RDBMS":
        _c.execute("""select database_role from v$database""")
        _data = _c.fetchone()
        conn_info['db_role'] = _data[0]
    else:
        # probably ASM or ASMPROXY
        conn_info['db_role'] = conn_info['instance_type']
    _c.close()

    return conn_info


def connect_string(config):
    """return connect string"""

    return config['username'] + "/" + config['password'] + "@" + \
        config['db_url']


def connect(_db, _c):
    """the actual connect"""

    if _c['role'].upper() == "SYSASM":
        _c['omode'] = _db.SYSASM

    if _c['role'].upper() == "SYSDBA":
        _c['omode'] = _db.SYSDBA
    _x = _db.connect(connect_string(_c), mode=_c['omode'])
    _x.module = _c['ME']

    return _x
