<?php
ini_set('display_errors', '1');
ini_set('display_startup_errors', '1');
error_reporting(E_ALL);
include_once(dirname(__FILE__) . "/utils/database.php");
include_once(dirname(__FILE__) . "/utils/password.php");

$json = file_get_contents('php://input');

$data = json_decode($json, true);

$email = $data["email"];
$password = $data["password"];
echo $password;
$hashed_password = hashPassword($password);


$db = new Database;
$db->query("INSERT INTO dms_users (email, password) VALUES (?, ?)", [$email, $hashed_password]);
$user_id = $db->getLastInsertedID();


session_start();

$_SESSION["user_id"] = $user_id;

echo json_encode(array("success" => true));
