---
layout: post
date: 2026-06-20
title: Open Source Summit India (2026)
---

I attended Open Source Summit India 2026 last week in [Mumbai](/photos/mumbai-india-2026). I wasn't speaking this time but attended quite a few interesting sessions. This post is a synthesized version of the notes I took over the two days of the conferences and some observations.

## Linus Torvalds & Dirk Hohndel

The biggest draw of this event was Linus Torvalds and his panel discussion with Dirk Hohndel. When asked about deprecating old hardware support from the kernel, he responded with "the cost of maintaining becomes too much at some point and it calls for deprecation". Further, he attributed the recent uptick in traffic during a merge window, partly to extensive AI use by developers. AI has been finding bugs that the maintainer feels should go as part of the imminent release, not later. During a merge window that is typically 2 weeks long, he merges ~200 requests, and avoids travelling during this time period which he considers a sacred focus block. He further went on to mention quite candidly that he's not a programmer anymore but that of a tech lead, so he naturally tries to understand the problem that a particular request is trying to patch. This is one of the reasons he emphasizes good commit messages as part of a request as that's the most critical part of the request for him, he's not reading much code lately.

Rust is now optional in git and will be a requirement in the next version of git. Linus is of the opinion that Rust in itself is not going to change the world, and that he's fairly biased towards C which he thinks is a much simpler language to write. But more importantly, Rust in Git is not an epoch moment as the internet would have you believe. In fact, there used to be a version of Git in Java that was developed for enterprise environment where Java was omnipresent.

Linus was also surprisingly not-hostile towards AI as has been the trend lately for some weird reason. He personally uses AI for his toy projects and thinks the kernel is much better off with AI finding security bugs that we should've found 20 years ago. Of course, it goes without saying that on the other side of this coin lies the AI slop problem which many open source projects are lately dealing with.

## Digiyatra

I'm a big fan of Digiyatra. It's one of those conveniences that you appreciate whenever you fly \[domestically] and so I was quite interested to understand what they have to do with Open Source. Because in all honestly, I was expecting corporate drivel but it was an insightful panel discussion.

Digiyatra for those who don't know is a system for streamlined security checks at major Indian airports primarily for domestic travel. The concept behind this idea was "my face as a boarding pass" or "face as a single token". They initially had a centralized storage system for all the customer's PII. But that changed during the global pandemic when they switched to a decentralized storage system where all the user data resided on the customer's phone. The customer would add its flight details close to the flight departure and the app would push the relevant data to the specific airport. This data is then removed shortly after the user's flight has departed. They also practice selective disclosure -- exposing/sharing only the data that's requested. For instance if there's a requirement to know the age of the user, just the birth date would do.

## Device Tree

This talk was an introduction to Linux Device Trees. It's a data format that describes non-discoverable hardware and is used by the linux kernel to understand the hardware it is running. The author explained Device Tree Source (DTS) and Devicetree Blob (DTB) before further delving into somewhat practical examples of how and when should one write DTSs. I would've loved if the talk had bridged the gap between what a DTS is and how I can use it, perhaps a minimal demo because the second half of the talk felt a little rushed but maybe that's just my lack of knowledge on the topic.

## Open Source Is Not the Same Anymore

This was an interesting--and slightly sensationalist imo--talk that claimed that the rules of the game have changed. In that Open Source is not the same it used to be a couple years back. They gave examples of curl shutting down its bug bounty program because of lots of AI slop, and Synadia taking back NATS from CNCF in hopes of relicensing it into a proprietary project, and finally the HashiCorp and Terraform license debacle. In due course though, Synadia backed off and OpenTofu was forked by the community. The point being "license stopped being the contract"; in the past ~5 years, Elastic, Terraform, Redis and NATS have all tried to or have moved their license. Which led the presenter to their next, bolder claim that "the community stopped being a community".

So they've proposed a set of 5 rules that new contributors can follow in order to gauge whether a project is worthy of their contributions. These rules included reading the license, effectively grepping for certain blacklisted terms, understanding if the bus or elephant factor of the project is not dangerously low, or sensing how quick the turnaround time of the maintainers on PRs or issues are, among 2 others. This idea of "gauging" a project's worthiness before beginning to contribute to it is something I found I didn't agree at all. I did have a discussion with the author after the session where I argued that if contributors had taken a look at the bus/elephant factor of Terraform before they started contributing, there might not have been an OpenTofu. Or on a more personal note, had I checked for Podman's bus/elephant factor, I wouldn't have contributed to it and eventually grown into a maintainer role. I believe contribution to open source projects should be motivated for the love of the game, not for second-order tangible outcomes such as one's future in the project.

I do agree that the five rules certainly help tell you about the hygiene of a project but that should never be your \[only] heuristic in deciding whether you should contribute to the project or not. If anything, I believe this hampers Open Source innovation. I should note that I had a constructive discussion with the author while discussing the same.

## Guide To Become Linux Kernel Maintainer

This was a full house, and ended up being a great simple, no-bs talk on how to best contribute to the Kernel. Drivers or subsystems are the best places for someone new to start with, there are countless orphaned subsystems that are in need of contributors, reviewers and maintainers. The kernel, in general, needs more and more reviewers especially now, with the advent of AI, the amount of contributors have grown significantly leading to increased burden on the maintainers.

## Kubernetes Networking: A packets journey across pods and nodes

I'm a big fan of talks that are practical in nature and try to demystify a technical concept or component; I've personally prepared and presented two such talks, namely [Build a Container Image from Scratch](/posts/build-a-container-image-from-scratch/) and [Build a Container Registry from Scratch](/posts/build-a-container-registry-from-scratch/). So I was quite excited about this talk and it absolutely didn't disappoint.

The crux of the talk was deciphering how pods connect with other pods either on the same node or on different nodes. We went through standard bridge+veth pairs to using TUN, to learning about ARP spoofing and flooding, overcoming that with VXLAN and finally calling it a day with using BGP via BIRD daemons. It was an extremely informative and interesting talk.

## Accelerating Innovation Through Open Source at Jio

I hadn't planned to attend this session but as this was a keynote that happened in the biggest hall where I also happened to be sitting at the back doing some work, I ended up getting some insights into the role that Open Source software plays at Jio. First and foremost, I appreciate a corporate as big as Jio on stage talking about how important Open Source is for them, because fluff or not, I believe that statements such as these at a keynote in one of the larger Open Source conferences must carry some impact.

On the technical front, I was surprised to know that Jio relies heavily on Container Images, they use some form of UBIs apparently but of course tuned and configured to suit their own specific needs. They have a Linux team who tunes the kernel config, slims down the kernel based on their requirements. It wasn't clear whether they contributed back to the kernel or not, at least I couldn't find Jio in the list of contributors on the [kernel stats page](https://insights.linuxfoundation.org/project/korg/contributors) at LF, please correct me if I'm wrong here.

## Rust & Linux

Keynote session by Greg Kroah-Hartman where he expounds the state of Rust in the Linux ecosystem, mainly the kernel. The basic premise is that while C is unforgiving, Rust makes it easy for developers to not make small mistakes and that directly translates to reviewers and maintainers focusing on more important bugs or issues, linking back to the same idea in one of the earlier talks where a need for more reviewers was discussed. Apart from the direct impact Rust is having, it's also changing the way C is being written in the kernel, adding a `guard()` method for instance for taking care of cleanup, somewhat similar to Go's `defer` I presume. Greg ended the talk with the idea that Rust will help make code reviewing easier in the future and that if the kernel were to be written in Rust, ~80% of the CVEs would be impossible. Throughout the talk I couldn't help but think about how different Linus's and Greg's views on Rust in Linux are. Linus sees nothing magical about Rust without being dismissive but at the same time Greg is extremely optimistic about the future of Rust in the kernel.

## Pruning Kernel CVEs With Code Reachability Analysis

This was a fun one as well. There has been a significant increase in the number of reported vulnerabilities in the Linux kernel. But not all of them affect the particular version of the kernel on that hardware with that set of config and kmodules, etc. For instance if you are notified of a vulnerability in the bluetooth subsystem but you don't build with bluetooth support, then that vulnerability doesn't really apply to you.

The author introduces a tool that attempts to evaluate for false positives by static analysis. It does so by evaluating Build time, runtime and system call reachability. There are plans to support VEX output and potentially expanding the scope to supporting language runtimes as well.

## Closing

Despite being more or less technical in theme, AI was the buzzword at the conference, for better or worse. Linus talked about it, Greg dismissed it, many presenters focused on it. Not that I wasn't expecting it but I was glad AI didn't really take the center stage at the conference, it was always on the sidelines save for a few talks.

This was the third Open Source Summit I've attended. I've spoken previously at the Japan and Europe editions in 2024 and 2025 respectively. I was an attendee this time around so I had ample time to attend all the sessions I wanted to and to engage in discussions with quite a few folks, which was "enlightening" in its own right.

I can't really compare this conf with either KubeCon or FOSDEM or any other major conferences for I'm yet to attend those. But all the sessions I attended were informative and insightful. I had one gripe with the whole event and that was the Solutions Showcase. It was bland at best, nowhere close to OSSEU or OSSJ and I hope future iterations of OSSI will have a more engaging, diverse and larger solutions showcase.
