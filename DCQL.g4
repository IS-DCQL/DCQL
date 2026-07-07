// 1. 定义一个名为 MysqlQuery 的语法
grammar MysqlQuery;


// 2. rule - 这是核心，表示规则，以 “:” 开始， “;” 结束， 多规则以 "|" 分隔。

// 2.1 lexer - 词法（符号(Token)名大写开头 - 词法）
AS                              : A S;
SELECT                       : S E L E C T;
FROM                        : F R O M;
TABLE                        : T A B L E;
MAX                         : M A X;
SUM                         : S U M;
AVG                          : A V G;
MIN                          : M I N;
COUNT                     : C O U N T;
ALL                            : A L L;
DISTINCT                  : D I S T I N C T;
WHERE                     : W H E R E;
GROUP                    : G R O U P;
BY                             : B Y ;
ORDER                     : O R D E R;
HAVING                   : H A V I N G;
NOT                          : N O T;
IS                               :  I S ;
TRUE                         : T R U E;
FALSE                        : F A L S E;
UNKNOWN               : U N K N O W N;
BETWEEN                  : B E T W E E N;
AND                           :  A N D;
IN                                :   I N;
NULL                           : N U L L;
OR                             : O R ;
ASC                          : A S C;
DESC                       : D E S C;
LIMIT                      : L I M I T ;
OFFSET                    : O F F S E T;
EXIST                    : E X I S T;
STARTWITH                    : S T A R T W I T H;
ENDWITH                    : E N D W I T H;
DESCRIBE                       : D E S C R I B E;
PRETTY                       : P R E T T Y;
EVERY                        : E V E R Y;
ANY                            : A N Y;
LIKE                           : L I K E;
TOP                            : T O P ;
BOTTOM                         : B O T T O M ;
CREATE                         :C R E A T E;
STRING                         :S T R I N G;
NUMBER                         :N U M B E R;
RANGE                          :R A N G E;
CHOICE                         :C H O I C E;
IMAGE                          :I M A G E;
FILE                           :F I L E;
ARRAY                          :A R R A Y;
CONTAINER                      :C O N T A I N E R;
GENERATOR                      :G E N E R A T O R;
ERROR                          :E R R O R;
MULTIPLE                       :M U L T I P L E;
TEMPLATE                    : T E M P L A T E;
TEMPLATES                   : T E M P L A T E S;
DROP                           :D R O P;
INSERT                         :I N S E R T;
INTO                           :I N T O;
VALUES                         :V A L U E S;
DELETE                         :D E L E T E;
UPDATE                         :U P D A T E;
SET                            :S E T;
ALTER                          :A L T E R;
ADD                            :A D D;
GRANT                          :G R A N T;
ON                             :O N;
TO                             :T O ;
REVOKE                         :R E V O K E;
SHOW                           :S H O W;
USER                           :U S E R;
USERS                          :U S E R S;
ROLE                           :R O L E;
ROLES                          :R O L E S;
RENAME                         :R E N A M E;
PASSWORD                       :P A S S W O R D;
WITH                           :W I T H;
PRIVILEGES                     :P R I V I L E G E S;
PUBLIC                         :P U B L I C;
UNIT                           :U N I T;
TYPE                           :T Y P E;
OPTION                         :O P T I O N;
OPTIONGROUP                    :O P T I O N G R O U P;
DATASET                        :D A T A S E T;

fragment A      : [aA];
fragment B      : [bB];
fragment C      : [cC];
fragment D      : [dD];
fragment E      : [eE];
fragment F      : [fF];
fragment G      : [gG];
fragment H      : [hH];
fragment I      : [iI];
fragment J      : [jJ];
fragment K      : [kK];
fragment L      : [lL];
fragment M      : [mM];
fragment N      : [nN];
fragment O      : [oO];
fragment P      : [pP];
fragment Q      : [qQ];
fragment R      : [rR];
fragment S      : [sS];
fragment T      : [tT];
fragment U      : [uU];
fragment V      : [vV];
fragment W      : [wW];
fragment X      : [xX];
fragment Y      : [yY];
fragment Z      : [zZ];
fragment HEX_DIGIT:                  [0-9A-F];
fragment DEC_DIGIT:                  [0-9];
fragment LETTER:                         [a-zA-Z];
fragment CHINESE_CHARACTER
    : [\u4E00-\u9FFF]
    ;

STRING_CONTENT:    '"'( 'A'..'Z' | 'a'..'z' | '_' | '$' | '%' | CHINESE_CHARACTER | '-' | DEC_DIGIT| '/'| '.')+'"';
ID:    ( 'A'..'Z' | 'a'..'z' | '_' | '$' | CHINESE_CHARACTER) ( 'A'..'Z' | 'a'..'z' | '_' | '$' | '0'..'9'| '-' | CHINESE_CHARACTER)*;
TEXT_STRING :    (  '\'' ( ('\\' '\\') | ('\'' '\'') | ('\\' '\'') | ~('\'') )* '\''  );
ID_LITERAL:   '*'|('@'|'_'|LETTER)(LETTER|DEC_DIGIT|'_')*;
REVERSE_QUOTE_ID :   '`' ~'`'+ '`';
DECIMAL_LITERAL:     DEC_DIGIT+'.'?DEC_DIGIT*;

// 2.2 parser - 语法
//解析规则(Parser rule)名小写开头,后面可以跟字母、数字、下划线 - 语法
templateName            : tmpName=ID;
column_name            :ID('[' decimalLiteral? ']')* ('.' ID ('[' decimalLiteral? ']')*)* ('.' ID)*;
function_name            : tmpName=ID ;
datasetName            : datName=ID;
unit_name              : ID ;
unit                   : ('(' unit_name ')')? ;
option_name            : ID ;
option_group_name      : ID ;

create_string_type     : STRING '(' column_name ')' ;
create_number_type     : NUMBER '(' column_name ','? (UNIT '=' unit_name)? ')' ;
create_range_type      : RANGE '(' column_name ','? (UNIT '=' unit_name)? ',' TYPE '=' (ERROR|RANGE) ')' ;
choice_type            : OPTION '=' '[' option_name (',' option_name)* ']' ;
choice_type_remove     : option_group_name '[' option_name (',' option_name)* ']' ;
choice_group_type      : OPTIONGROUP '=' '[' choice_type_remove (',' choice_type_remove)* ']' ;
create_choice_type     : CHOICE '(' column_name ','? (choice_type|choice_group_type) ')' ;
create_image_type      : IMAGE '(' column_name ')' ;
create_file_type       : FILE '(' column_name ')' ;

create_table_type      : TABLE '(' column_name ')' '.' create_unnested_type |
                         TABLE '(' column_name (',' create_unnested_type)+ ')' ;
array_type             : STRING |
                         NUMBER '(' (UNIT '=' unit_name)? ')' |
                         RANGE '(' (UNIT '=' unit_name)? ','? TYPE '=' (ERROR|RANGE) ')' |
                         CHOICE '(' choice_type ')' | CHOICE '(' choice_group_type ')' |
                         IMAGE | FILE |
                         TABLE '.' create_unnested_type |
                         TABLE '(' create_unnested_type (',' create_unnested_type)* ')' |
                         CONTAINER '.' create_all_type |
                         CONTAINER '(' create_all_type (',' create_all_type)* ')' |
                         GENERATOR '.' generator_type |
                         GENERATOR '(' generator_type (',' generator_type)* ')' ;
create_array_type      : ARRAY '(' column_name ')' '.' array_type |
                         ARRAY '(' column_name ',' array_type ')' ;
create_container_type  : CONTAINER '(' column_name ')' '.' create_all_type |
                         CONTAINER '(' column_name (',' create_all_type)+ ')' ;
generator_type         : create_unnested_type | create_table_type | create_array_type |create_container_type ;
create_generator_type  : GENERATOR '(' column_name ')' '.' generator_type |
                         GENERATOR '(' column_name (',' generator_type)+ ')' ;

insert_string_value_remove    : value ;
insert_number_value_remove    : decimalLiteral ;
insert_range_value_remove     : '(' decimalLiteral ',' decimalLiteral ')' ;
insert_choice_value_remove    : option_name | option_group_name '(' option_name ')' ;
insert_image_value_remove     : pathText | '(' pathText (',' pathText)* ')' ;
insert_file_value_remove      : pathText | '(' pathText (',' pathText)* ')' ;
insert_table_value_remove     : '(' table_row (',' table_row)* ')' ;
insert_container_value_remove : '(' container_element (',' container_element)* ')';
insert_generator_value_remove : '(' generator_element (',' generator_element)* ')';

insert_string_value           : STRING value ;
insert_number_value           : NUMBER decimalLiteral ;
insert_range_value            : RANGE TYPE '=' (ERROR|RANGE) '(' decimalLiteral ',' decimalLiteral ')' ;
insert_choice_value           : CHOICE (option_name | option_group_name '(' option_name ')') ;
insert_image_value            : IMAGE (pathText | '(' pathText (',' pathText)+ ')') ;
insert_file_value             : FILE  (pathText | '(' pathText (',' pathText)+ ')') ;
table_row                     : '(' insert_unnested_value (',' (insert_unnested_value | NULL))* ')' ;
insert_table_value            : TABLE  (column_name(',' column_name)*)? '(' table_row (',' table_row)* ')' ;

array_element_string          : STRING '[' insert_string_value_remove (',' insert_string_value_remove)* ']' ;
array_element_number          : NUMBER '[' insert_number_value_remove (',' insert_number_value_remove)* ']' ;
array_element_range           : (RANGE|ERROR) '[' insert_range_value_remove (',' insert_range_value_remove)* ']' ;
array_element_choice          : CHOICE '[' insert_choice_value_remove (',' insert_choice_value_remove)* ']' ;
array_element_image           : IMAGE '[' insert_image_value_remove (',' insert_image_value_remove)* ']' ;
array_element_file            : FILE '[' insert_file_value_remove (',' insert_file_value_remove)* ']' ;
array_element_table           : TABLE '[' insert_table_value_remove (',' insert_table_value_remove)* ']' ;
array_element_container       : CONTAINER '[' insert_container_value_remove (',' insert_container_value_remove)* ']' ;
array_element_generator       : GENERATOR '[' insert_generator_value_remove (',' insert_generator_value_remove)* ']' ;
insert_array_value            : ARRAY (array_element_string | array_element_number |array_element_range |
                                       array_element_choice | array_element_image | array_element_file |
                                       array_element_table | array_element_container | array_element_generator) ;

container_element             : insert_all_value;
insert_container_value        : CONTAINER (column_name(',' column_name)*)? '(' container_element (',' container_element)* ')';

generator_element             : insert_string_value | insert_number_value | insert_range_value |
                                insert_choice_value | insert_image_value | insert_file_value |
                                insert_table_value | insert_array_value | insert_container_value ;
insert_generator_value        : GENERATOR  column_name generator_element ;


 simpleStatement:
 selectStatement
 | describeStatement
 |  createTemplateStatement
 | dropTemplateStatement
 | insertStatement
 | updateStatement
 | deleteStatement
 | alterTemplateStatement
 | controlStatement
 | createDatasetStatement
 | dropDatasetStatement
 | alterDatastStatement
 ;
//dataset
createDatasetStatement             : CREATE DATASET datasetName TEMPLATE templateName;
dropDatasetStatement               : DROP DATASET datasetName TEMPLATE templateName;
alterDatastStatement               : ALTER DATASET datasetName ',' datasetName ;
//controlStatement
controlStatement     : create_role | drop_role | rename_role | grant_privilege_to_role | revoke_privilege_from_role | show_role |
                       create_user | drop_user | rename_user | update_user_password | grant_role_to_user |
                       revoke_role_from_user | show_user ;
role_name                          : ID ;
user_name                          : ID ;
password                           : ID ;
action                             : CREATE | DROP | ALTER | DESCRIBE | INSERT | DELETE | UPDATE | SELECT |
                                     RENAME | SHOW | ALL ;
resource                           : TEMPLATE templateName? | TEMPLATES | ROLE role_name? | ROLES (WITH GRANT)? |
                                     USER user_name? (WITH ROLE | WITH PASSWORD)? | USERS (WITH ROLE | WITH PASSWORD)? ;
privilege                          : action ON resource | ALL PRIVILEGES ;

create_role                        : CREATE ROLE role_name WITH  (role_name (',' role_name)*)?  ','?
                                     (privilege (',' privilege)*)? ;
drop_role                          : DROP ROLE role_name (',' role_name)* ;
rename_role                        : RENAME ROLE role_name ',' role_name ;
grant_privilege_to_role            : GRANT (privilege (',' privilege)* TO role_name |
                                            privilege TO role_name (',' role_name)*) ;
revoke_privilege_from_role         : REVOKE (privilege (',' privilege)* FROM role_name |
                                             privilege FROM role_name (',' role_name)*) ;
show_role                          : SHOW (ROLE role_name (',' role_name)* | ROLES (WITH GRANT)?) ;

create_user                        : CREATE USER user_name WITH PASSWORD password ',' ROLE role_name (',' role_name)*;
drop_user                          : DROP USER user_name (',' user_name)* ;
rename_user                        : RENAME USER user_name ',' user_name ;
update_user_password               : UPDATE USER user_name WITH PASSWORD password ',' password ;
grant_role_to_user                 : GRANT (role_name (',' role_name)* TO (user_name|PUBLIC) |
                                            role_name TO (user_name (',' user_name)*|PUBLIC)) ;
revoke_role_from_user              : REVOKE (role_name (',' role_name)* FROM (user_name|PUBLIC) |
                                             role_name FROM (user_name (',' user_name)*|PUBLIC)) ;
show_user                          : SHOW (USER user_name (',' user_name)* | USERS) WITH
                                     (PASSWORD (',' ROLE)? | ROLE (',' PASSWORD)?) ;
//alterStatement
alterTemplateStatement       : ALTER TEMPLATE templateName (',' templateName)? alterStatements (',' alterStatements)* ;
alterStatements                    : add_content | drop_content | alter_content ;
add_content                        : ADD add_contents (',' add_contents)* ;
add_contents                       : create_all_type ;
drop_content                       : DROP drop_contents (',' drop_contents)* ;
drop_contents                      : column_name (choice_type | choice_group_type)? unit ;
alter_content                      : ALTER alter_contents (',' alter_contents)* ;
alter_contents                     : (column_name ',' column_name) | (column_name unit ',' unit) |
                                      column_name (choice_type | choice_group_type) ',' (choice_type | choice_group_type) ;
//updateStatement,deleteStatement,dropStatement
updateStatement      : UPDATE TEMPLATE templateName DATASET datasetName SET column_name '=' value whereClause? ;
deleteStatement      : DELETE FROM TEMPLATE templateName DATASET datasetName whereClause? ;
dropTemplateStatement:
    DROP TEMPLATE templateName
;
//insertStatement
insertStatement:
    INSERT INTO TEMPLATE templateName DATASET datasetName ('(' column_name (',' column_name)* ')')?
    VALUES '(' insert_all_values ')' (',' '(' insert_all_values ')')*
;

insert_all_values             : insert_all_value (',' (insert_all_value | insert_attribute = NULL))* ;
insert_all_value              : insert_unnested_value | insert_nested_value ;
insert_unnested_value         : insert_string_value | insert_number_value | insert_range_value |
                                insert_choice_value | insert_image_value | insert_file_value ;
insert_nested_value           : insert_table_value | insert_array_value | insert_container_value | insert_generator_value ;
//createStatement
 createTemplateStatement:
    CREATE TEMPLATE templateName
        create_all_type (',' create_all_type)*
;

create_all_type        : create_unnested_type | create_nested_type;
create_unnested_type   : create_string_type | create_number_type | create_range_type | create_choice_type | create_image_type | create_file_type;
create_nested_type     : create_table_type | create_array_type | create_container_type | create_generator_type;
//selectStatement
 selectStatement:
       SELECT
        selectElements
    (
        FROM TEMPLATE tableSources
        (DATASET datasetName)?
        ( whereClause )?
        ( groupByCaluse )?
        ( havingCaluse )?
    ) ?
    ( orderByClause )?
    ( limitClause )?
;
//describeStatement
 describeStatement:
    DESCRIBE templateName
 ;

 selectElements
    : (star='*' | selectElement ) (',' selectElement)*
    ;


tableSources
    : templateName |  templateName '(' column_name ')' (',' templateName '(' column_name ')')+
    ;

whereClause
    : WHERE    logicExpression
    ;

 logicExpression
     : logicExpression logicalOperator logicExpression
     | leafLogicExpression
     | (EVERY | ANY)? '(' logicExpression ')'
     | column_name
     ;

 leafLogicExpression: (ALL | EXIST)? (comparisonLeafLogicExpression | setLeafLogicExpression | judgeLeafLogicExpression | matchLeafLogicExpression);
 comparisonLeafLogicExpression: (TOP | BOTTOM)? fullColumnName comparisonOperator value ;
 setLeafLogicExpression: fullColumnName NOT? comparisonOperator '(' value (',' value)*  ')' ;
 judgeLeafLogicExpression: column_name IS NOT? value;
 matchLeafLogicExpression: column_name NOT? LIKE value;

groupByCaluse
    :   GROUP BY   groupByItem (',' groupByItem)*
    ;
havingCaluse
    :    HAVING  logicExpression
   ;

 orderByClause
    : ORDER BY orderByExpression (',' orderByExpression)*
    ;

 limitClause
    : LIMIT
    (
      (offset=decimalLiteral ',')? limit=decimalLiteral
      | limit=decimalLiteral OFFSET offset=decimalLiteral
    )
    ;

orderByExpression
    : fullColumnName order=(ASC | DESC)?
    ;



groupByItem
    : fullColumnName order=(ASC | DESC)?
    ;

logicalOperator
    : AND | '&' '&'  | OR | '|' '|'
    ;

comparisonOperator
    : '=' | '>' | '<' | '<' '=' | '>' '='
    | '<' '>' | '!' '=' | '<' '=' '>' | STARTWITH | ENDWITH | LIKE | IS | IN | NOT LIKE | NOT IN | IS NOT
    ;


value
    : uid
    | textLiteral
    | decimalLiteral | NULL
    ;

decimalLiteral
    : DECIMAL_LITERAL
    ;
textLiteral
    : TEXT_STRING
    ;

selectElement
    : distinct=ID? fullColumnName (AS? uid)?      #selectColumnElement
    | functionCall (AS? uid)?               #selectFunctionElement
    ;


fullColumnName
    : column_name
    ;

functionCall
   :  aggregateWindowedFunction     #aggregateFunctionCall
    ;

aggregateWindowedFunction
    : (AVG | MAX | MIN | SUM) '(' functionArg ')'
    | COUNT '(' (starArg='*' |  functionArg?) ')'
    | COUNT '(' aggregator=DISTINCT functionArgs ')'
    ;

functionArg
    :  column_name
    ;

functionArgs
    : column_name (',' column_name)*
    ;

uid
    : ID
    ;

stringText
    : STRING_CONTENT
    ;
pathText : STRING_CONTENT ;

// 在进行解析的过程中，忽略掉空格，换行
WS : [ \t\r\n]+ -> skip ; // skip spaces, tabs, newlines
