async function hashPassword(password, salt) {
    if (!password || typeof password !== 'string') {
        throw new Error('Password must be a non-empty string');
    }
    if (!(salt instanceof Uint8Array) || salt.length !== 16) {
        throw new Error('Salt must be a Uint8Array of length 16');
    }

    const encoder = new TextEncoder();
    const passwordBuffer = encoder.encode(password);

    try {
        const keyMaterial = await window.crypto.subtle.importKey(
            "raw",
            passwordBuffer,
            { name: "PBKDF2" },
            false,
            ["deriveBits"]
        );

        const derivedBits = await window.crypto.subtle.deriveBits(
            {
                name: "PBKDF2",
                salt: salt,
                iterations: 100000,
                hash: "SHA-256",
            },
            keyMaterial,
            256
        );

        const hashArray = Array.from(new Uint8Array(derivedBits));
        const hashHex = hashArray
            .map((b) => b.toString(16).padStart(2, "0"))
            .join("");

        return hashHex;
    } catch (error) {
        console.error('Error in hashPassword:', error);
        throw error;
    }
}
