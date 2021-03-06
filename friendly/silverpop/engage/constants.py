
LIST_VISIBILITY_PRIVATE = 0
LIST_VISIBILITY_SHARED = 1

LIST_VISIBILITY_CHOICES = (
    LIST_VISIBILITY_PRIVATE,
    LIST_VISIBILITY_SHARED,
)

LIST_TYPE_DATABASE = 0
LIST_TYPE_QUERY = 1
LIST_TYPE_DATABASE_CONTACT_QUERY = 2
LIST_TYPE_TEST_LIST = 5
LIST_TYPE_SEED_LIST = 6
LIST_TYPE_SUPPRESSION_LIST = 13
LIST_TYPE_RELATIONAL_TABLE = 15
LIST_TYPE_CONTACT_LIST = 18

COLUMN_TYPE_TEXT = 0
COLUMN_TYPE_YESNO = 1
COLUMN_TYPE_NUMERIC = 2
COLUMN_TYPE_DATE = 3
COLUMN_TYPE_TIME = 4
COLUMN_TYPE_COUNTRY = 5
COLUMN_TYPE_SELECTION = 6
COLUMN_TYPE_SEGMENTING = 8
COLUMN_TYPE_SYSTEM = 9
COLUMN_TYPE_SMS_OPT_OUT_DATE = 14
COLUMN_TYPE_SMS_PHONE_NUMBER = 15
COLUMN_TYPE_PHONE_NUMBER = 16
COLUMN_TYPE_TIMESTAMP = 17
COLUMN_TYPE_MULTI_SELECT = 20

COLUMN_TYPE_CHOICES = (
    COLUMN_TYPE_TEXT,
    COLUMN_TYPE_YESNO,
    COLUMN_TYPE_NUMERIC,
    COLUMN_TYPE_DATE,
    COLUMN_TYPE_TIME,
    COLUMN_TYPE_COUNTRY,
    COLUMN_TYPE_SELECTION,
    COLUMN_TYPE_SEGMENTING,
    COLUMN_TYPE_SYSTEM,
    COLUMN_TYPE_SMS_OPT_OUT_DATE,
    COLUMN_TYPE_SMS_PHONE_NUMBER,
    COLUMN_TYPE_PHONE_NUMBER,
    COLUMN_TYPE_TIMESTAMP,
    COLUMN_TYPE_MULTI_SELECT,
)

CONTACT_CREATED_FROM_DATABASE = 0
CONTACT_CREATED_MANUALLY = 1
CONTACT_CREATED_OPTED_IN = 2
CONTACT_CREATED_FROM_TRACKING_DB = 3

ERR_RECIPIENT_ALREADY_EXISTS = 122
ERR_RECIPIENT_IS_NOT_A_MEMBER = 128
ERR_SESSION_EXPIRED_OR_INVALID = 145
ERR_COLUMN_ALREADY_EXISTS = 201
ERR_CONTACT_LIST_NAME_ALREADY_EXISTS = 256

EXPORT_TYPE_ALL = 'ALL'
EXPORT_TYPE_OPT_IN = 'OPT_IN'
EXPORT_TYPE_OPT_OUT = 'OPT_OUT'
EXPORT_TYPE_UNDELIVERABLE = 'UNDELIVERABLE'

EXPORT_FORMAT_CSV = 'CSV'
EXPORT_FORMAT_TAB = 'TAB'
EXPORT_FORMAT_PIPE = 'PIPE'

#ERRORS = (
#    (ERR_RECIPIENT_IS_NOT_A_MEMBER, EngageError),
#    (ERR_SESSION_EXPIRED_OR_INVALID, EngageError),
#)