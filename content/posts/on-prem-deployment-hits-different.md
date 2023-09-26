---
title: "On Prem Deployments Hits Different"
date: 2023-09-24T11:34:59+05:30
draft: false
ShowToc: true
# TocOpen: true
# ShowRelatedContent: false
summary: "My first experience with on-prem deployment and also my first travel outside India."
tags: ["qure.ai"]
categories: ["work"]
cover:
    image: "/images/posts/on-prem-deployment-hits-different/cover-image.jpg"
    alt: "Fiji Islands"
    caption: "[Fiji Islands Photo by Damon Hall](https://www.pexels.com/photo/aerial-view-of-beach-and-huts-1752461/)"
    relative: false
---
### Introduction 

I had the incredible opportunity to embark on a journey to the picturesque Fiji Islands in July, representing my company, Qure.ai. This adventure marked my first-ever international trip, and I was bubbling with excitement at the prospect of obtaining that coveted seal on my passport. Fiji, with its breathtaking natural beauty, was everything I had dreamed of and more.

Nestled in the heart of the South Pacific Ocean, Fiji is renowned for its lush landscapes, crystal-clear waters, and vibrant coral reefs. The pristine beaches and tropical forests were a feast for the senses, offering a serene escape from the bustling city life I was accustomed to back in India. From exploring hidden waterfalls to snorkeling in vibrant underwater gardens, Fiji's natural wonders left an indelible mark on my travel experience.

### The Mission  

However, my journey to Fiji was not just about leisure; it was a business trip with two members representing our company, **[Qure.ai](https://www.qure.ai/)**, on this mission. I, as a Site Reliability Engineer (SRE), took on the responsibility of representing the engineering team and overseeing the deployment process. Alongside me, [Mr. Anmol Karthik Prabhu](https://www.linkedin.com/in/anmol-karthik-prabhu-clssgb%E2%84%A2-msc-bme-660627113/) from the Client Success team played a crucial role in coordinating with the UNDP team.

At Qure.ai, we specialize in providing innovative healthcare solutions, and this time, our focus was on an on-premises deployment. This deployment approach ensures that our product operates seamlessly without the need for an internet connection, making it accessible to even the most remote locations across the globe.

Our deployment strategy involved setting up Docker containers on a compact, yet powerful NUC (Next Unit of Computing) device with Ubuntu flashed on it. We call this NUC as **qbox** where 'q' - denotes the name qure.ai. This offline setup allows our clients to utilize our product without relying on the internet, making healthcare accessible in places where connectivity is scarce. The technical challenges that arose during this deployment tested our skills and creativity, pushing us to find innovative solutions to ensure a smooth installation process.

Collaborating with us on this ambitious endeavor was the **United Nations Development Programme (UNDP)**, a global organization dedicated to addressing critical issues and fostering sustainable development worldwide. Their partnership was instrumental in hosting this deployment in Fiji, where access to advanced healthcare solutions is crucial.

### The Deployment

<<<<<<< HEAD
Deployment in Fiji was scheduled for five days, and our journey began on July 28th when we flew from Mumbai to Fiji, finally arriving on the 30th. On Monday, August 31st, we commenced our deployments and conducted training sessions for X-ray technicians from various Pacific Islands. The diversity of attendees added a unique dimension to our mission, fostering cross-cultural exchanges and cooperation.

On the night of Sunday, August 30th, I found myself in my hotel room with four q-boxes. I was able to complete the deployment setup on all the 4 boxes without much issues using the script we had prepared. The next day, we were joined by the UNDP team, and we began workshops.

{{< figure src="/images/posts/on-prem-deployment-hits-different/image-8.jpg#center" title="Setting up the qboxes with dockers" caption="Fiji Deployment Days" link="/images/posts/on-prem-deployment-hits-different/image-8.jpg" target="_blank" class="align-center" >}}

The next crucial step involved was integrating our NUC boxes, affectionately known as **"Qboxes"**, with the **[Fujifilm setup](https://xairbyfujifilm.com/)**. We received virtual assistance from Fujifilm experts, which enabled us to complete the deployment setups for all four boxes within just two days. This rapid progress was a testament to the collaborative spirit that underpinned our mission.

Simultaneously, we commenced training sessions for the X-ray technicians who had attended the event. These Qboxes were designed to be transported to their respective islands where internet connectivity is often limited or non-existent, thus empowering remote communities with access to vital healthcare services.

Some photo dumps from the deployment

{{< figure src="/images/posts/on-prem-deployment-hits-different/image-4.jpg#center" title="The entire team with the UNDP officials" caption="Fiji Deployment Days" link="/images/posts/on-prem-deployment-hits-different/image-4.jpg" target="_blank" class="align-center" >}}

{{< figure src="/images/posts/on-prem-deployment-hits-different/image-5.jpg#center" title="Qure Boys" caption="Fiji Deployment Days" link="/images/posts/on-prem-deployment-hits-different/image-5.jpg" target="_blank" class="align-center" >}}

{{< figure src="/images/posts/on-prem-deployment-hits-different/image-1.jpg#center" title="Me explaining our qtrack to X-ray techs" caption="Fiji Deployment Days" link="/images/posts/on-prem-deployment-hits-different/image-1.jpg" target="_blank" class="align-center" >}}

{{< figure src="/images/posts/on-prem-deployment-hits-different/image-2.jpg#center" title="Workshop" caption="Fiji Deployment Days" link="/images/posts/on-prem-deployment-hits-different/image-2.jpg" target="_blank" class="align-center" >}}

{{< figure src="/images/posts/on-prem-deployment-hits-different/image-7.jpg#center" title="Workshop" caption="Fiji Deployment Days" link="/images/posts/on-prem-deployment-hits-different/image-7.jpg" target="_blank" class="align-center" >}}

{{< figure src="/images/posts/on-prem-deployment-hits-different/image-3.jpg#center" title="Just show off lol" caption="Fiji Deployment Days" link="/images/posts/on-prem-deployment-hits-different/image-3.jpg" target="_blank" class="align-center" >}}

{{< figure src="/images/posts/on-prem-deployment-hits-different/image-6.jpg#center" title="Photobombing Sessions" caption="Fiji Deployment Days" link="/images/posts/on-prem-deployment-hits-different/image-6.jpg" target="_blank" class="align-center" >}}


### Exploring Fiji

As our mission drew to a close, we seized the opportunity on the last day, Friday, August 4th, to explore some of Fiji's treasures. Together with Praneel, a UNDP official, we ventured to private islands and visited a shipyard. The serene beaches and breathtaking natural beauty of Fiji left an indelible mark on our hearts, offering a glimpse into the paradise that the country is renowned for. Wait for my Fiji specific blog lol.

### The Experience

Fiji was one of a kind experience for me as it was my first international travel. The food, people and the culture was so different from what I have experienced in India. The people were so friendly and welcoming. The food was delicious and the culture was so vibrant. I will be writing a separate blog post about my experience in Fiji.

### Qure.ai's Impact

Qure.ai was founded in 2016. Our mission is to use artificial intelligence to make healthcare more accessible and affordable.

Qure.ai, is at the forefront of revolutionizing healthcare through artificial intelligence. Our mission is to make healthcare more accessible and efficient through cutting-edge technology. This deployment in Fiji was yet another step toward achieving this goal, bringing healthcare solutions to those who need it most.  

I just wrote about the deployment stuffs here, Fiji travel experience will be a separate blog post. Stay tuned for that!