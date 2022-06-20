# Spring '83 Notes

## 2022-06-17

Here are some thoughts and feedback that I have on the [Spring '83 Draft Spec](https://github.com/robinsloan/spring-83-spec)
after implementing a server for it. These are mostly focused on stripping out/simplifying things because that's kind of what I'm into
[[0]](https://portal.mozz.us/spartan/spartan.mozz.us/). I see a new draft version was published yesterday, but so far
I have only skimmed it for changes.

### Overall

It was a fun project and a nice opportunity for me to write a small, self-contained server using django.
I appreciate that being built on top of HTTP means I can use off-the-shelf libraries. Ed25519 is nice
and way easier to work with than something like TLS + OpenSSL.

I think "Spring '83" is a great name for a protocol and really encapsulates the vibe of the newsletter post.

### Terminology

The terminology section is really awesome for establishing common vocabulary and was a helpful reference when I was writing my server.

### Validating Board Timestamps

> The If-Unmodified-Since header is transmitted as a convenience for caches and other intermediaries.
> 
> that "speak HTTP". The server must disregard it. The "real" timestamp -- the one that will be verified
> cryptographically -- is transmitted as part of the board HTML. The client must include a <time> element
> with its datetime attribute set to a UTC timestamp in ISO 8601 format, without milliseconds: YYYY-MM-DDTHH:MM:SSZ.

Embedding the timestamp in the HTML is a pain for obvious reasons.
  
Try this... Instead of signing the board content (`sign(<board>)`), sign the board content concatenated
with the If-Unmodified-Since header value (`sign(<board> + <last-modified-date>)`). Now
servers can verify the header hasn't been modified, authors don't need to waste their precious 2217 bytes
on meta tags, and I can delete like 30 lines of HTML parsing and validation from my codebase. 

### Prefer: respond-async
  
I was going to comment that I think this header is unnecessary, but it looks like it was already taken out. 🥳
  
### Difficulty Factor
  
I think the whole concept is unnecessary and I would probably not implement it or just always return `0`.
  
If taken at face value, one issue is that all servers share the same difficulty factor.
Having each server seed their formula with a random number might be an improvement.
  
### Enumerating Keys
  
> Finally, the server must not enumerate keys or boards for any requester; the server must only respond to requests for specific keys.

I get where you're coming, from but you can't really mandate something like this. I mean, you can try, but people will generally do whatever
the hell they want anyway. It kind of feels like saying "Clients must not exploit vulnerabilities in servers". If only it were that easy...
  
### Key Rotation
  
I *really* like the hashcan algorithm, but not the expiration part
  
> This expiration policy makes key rotation mandatory over the long term. Clients may implement features that make the process more
> convenient, even automatic, but the recurring "stress test" on the publisher-follower link is a feature, not a bug. The goal is to
>  keep Spring '83 relationships "live" and engaged, with fresh opt-ins every two years at most.

Key rotation just doesn't work without a trust authority. Gemini learned this the hard way with self-signed TLS certificates. After three
years they/we still haven't been able to figure out what to do when a certificate expires.

The schemes that folks inevitably come up with (some variation of signing the new key with the old key) provide zero
security benefit and only obfuscate what's going on which is arguably worse than nothing. It drives me absolutely crazy.
  
You MUST place trust in some third-party in order to do key rotation, like PKI does with Certificate Authorities. The catch-22 is that once you
have that setup, you're better off ditching self-signed entirely and having the third-party manage the keys in the first place like CAs do.
*I would LOVE to be proven wrong here.*

My advice is to drop the key expiration and embrace the limitations of what a self-signed certificate is.
No compromises. Your identity is your keypair. Your identity is your keypair.
