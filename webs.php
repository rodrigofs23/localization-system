<?php
 
// get the HTTP method, path and body of the request
$method = $_SERVER['REQUEST_METHOD'];
$request = explode('/', trim($_SERVER['PATH_INFO'],'/'));
$input = json_decode(file_get_contents('php://input'),true);
 
// connect to the mysql database
$link = mysqli_connect('localhost', 'sergiool', 'kedma256', 'ibeacon');
mysqli_set_charset($link,'utf8');
 
// retrieve the table and key from the path
$table = array_shift($request);
$key = array_shift($request);
 
if ($input) {
   // escape the columns and values from the input object
   $columns = array_keys($input);
   $values = array_values($input); 
 
   // build the SET part of the SQL command
   $set = '';
   for ($i=0;$i<count($columns);$i++) {
     $set.=($i>0?',':'').'`'.$columns[$i].'`=';
     $set.=($values[$i]===null?'NULL':'"'.$values[$i].'"');
   }
}
 
// create SQL based on HTTP method
switch ($method) {
  case 'GET':
    $sql = "SELECT mac, x, y from `$table` where hora in (SELECT max(hora) FROM `$table` WHERE hora > subtime(NOW(), '5') group by mac)".($key?" AND mac='$key'":''); break;
  case 'PUT':
    $sql = "update `$table` set $set where id=$key"; break;
  case 'POST':
    $sql = "insert into `$table` set $set"; break;
  case 'DELETE':
    $sql = "delete from `$table` where id=$key"; break;
}

#echo ($sql);
 
// excecute SQL statement
$result = mysqli_query($link,$sql);
 
// die if SQL statement failed
if (!$result) {
  http_response_code(404);
  die(mysqli_error($link));
}

// print results, insert id or affected row count
if ($method == 'GET') {
  if (!$key) echo '[';
  for ($i=0;$i<mysqli_num_rows($result);$i++) {
    echo ($i>0?',':'').json_encode(mysqli_fetch_object($result));
  }
  if (!$key) echo ']';
} elseif ($method == 'POST') {
  echo mysqli_insert_id($link);
} else {
  echo mysqli_affected_rows($link);
}
 
// close mysql connection
mysqli_close($link);
?>
