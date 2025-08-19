<?php
function verifyPassword($inputPassword, $storedHash)
{
    $hashedInput = hashPassword($inputPassword);
    echo $hashedInput;
    return hash_equals($storedHash, $hashedInput);
}

function hashPassword($password)
{
    return password_hash($password, PASSWORD_DEFAULT);
}