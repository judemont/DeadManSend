<?php

ini_set('display_errors', '1');
ini_set('display_startup_errors', '1');
error_reporting(E_ALL);
include_once(dirname(__FILE__) . "/utils/database.php");
include_once(dirname(__FILE__) . "/utils/password.php");

header('Content-Type: application/json');

$data = json_decode(file_get_contents('php://input'), true);
$email = $data['email'];
$password = $data['password'];
$rememberMe = $data['rememberMe'] ?? false;

if (empty($email) || empty($password)) {
    http_response_code(400);
    echo json_encode(['message' => 'Email and password are required']);
    exit;
}   

$db = new Database;

$user = $db->select('SELECT id, password FROM dms_users WHERE email = ?', [$email])[0];


if (!$user) {
    http_response_code(401);
    echo json_encode(['message' => 'Invalid email or password']);
    exit;
}


echo $user['password'];
echo $password;
if (!verifyPassword($user['password'], $password)) {
    http_response_code(401);
    echo json_encode(['message' => 'Invalid email or password']);
    exit;
}

session_start();
$_SESSION['user_id'] = $user['id'];

echo json_encode(array("success" => true));


