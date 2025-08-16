<?php
function verifyPassword($inputPassword, $storedHash, $storedSaltHex)
{
    // Convert the hex salt back to binary
    $salt = hex2bin($storedSaltHex);
    // PBKDF2 parameters (must match those used in JavaScript)
    $iterations = 100000;
    $hashAlgorithm = 'sha256';
    $keyLength = 32; // 256 bits

    // Hash the input password with the stored salt
    $hashedInput = hash_pbkdf2(
        $hashAlgorithm,
        $inputPassword,
        $salt,
        $iterations,
        $keyLength,
        true // Return raw binary output
    );

    // Convert the binary hash to hex for comparison
    $hashedInputHex1 = bin2hex($hashedInput);
    $hashedInputHex2 = hashPassword($hashedInputHex1);
    // Compare the newly generated hash with the stored hash
    return hash_equals($storedHash, $hashedInputHex2);
}

function hashPassword($password)
{
    return password_hash($password, PASSWORD_DEFAULT);
}