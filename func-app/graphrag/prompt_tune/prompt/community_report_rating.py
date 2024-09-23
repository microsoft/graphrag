# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Fine tuning prompts for Community Reports Rating."""

GENERATE_REPORT_RATING_PROMPT = """

You are a helpful agent tasked with rating the importance of a given text in the context of the provided domain and persona. Your goal is to provide a rating that reflects the relevance and significance of the text to the specified domain and persona. Use your expertise to evaluate the text based on the importance criteria and assign a float score between 0-10. Only respond with the text description of the importance criteria. Use the provided example data format to guide your response. Ignore the content of the example data and focus on the structure.

######################
-Examples-
######################

### Example 1

# Domain

Personal and Family Communication

# Persona

You are an expert in Social Network Analysis with a focus on the Personal and Family Communication domain. You are skilled at mapping and interpreting complex social networks, understanding the dynamics of interpersonal relationships, and identifying patterns of communication within communities. You are adept at helping people understand the structure and relations within their personal and family networks, providing insights into how information flows, how strong various connections are, and how these networks influence individual and group behavior.

# Data


Subject: Re: Event
From: Alice Brown alice.brown@example.com
Date: 2012-11-14, 9:52 a.m.
To: John Smith john.smith@example.com
CC: Jane Doe jane.doe@example.com, Bob Johnson bob.johnson@example.com, Emma Davis emma.davis@example.com

The event is at 6pm at City Hall (Queen street) event chamber. We
just need to get there by 5:45pm. It is 30-minute long so we will be
done by 6:30pm. We'll then head over to New Sky on Spadina for some
unique cuisine!

Guests are you and Emma, and my uncle and auntie from London
who my folks have designated to act as their reps. Jane and Joe are
witnesses.

Be there or be square!
Alice

On Wed, Nov 14, 2012 at 9:40 AM, John Smith john.smith@example.com wrote:

Thats the day after Bob's event!
Any more details on the event schedule? ITS NEXT WEEK!
On Tue, Nov 13, 2012 at 7:51 PM, Jane Doe
jane.doe@example.com wrote:
I am supposed to forward you the invitation to this year's celebration.
Date: Saturday, Nov. 24, 6 pm starting
Place as usual: Dean's house, 6 Cardish, Kleinburg L0J 1C0
Jane Doe
jane.doe@example.com

# Importance Criteria

A float score between 0-10 that represents the relevance of the email's content to family communication, health concerns, travel plans, and interpersonal dynamics, with 1 being trivial or spam and 10 being highly relevant, urgent, and impactful to family cohesion or well-being.
#############################

### Example 2

# Domain

Literary Analysis

# Persona

You are a literary scholar with a focus on works from the 19th century. You are skilled at analyzing and interpreting texts, identifying themes and motifs, and understanding the historical and cultural contexts in which these works were written. You are adept at helping people understand the deeper meanings and significance of literary works, providing insights into the author's intentions, the social issues addressed in the text, and the impact of these works on contemporary society.

# Data

Had she found Jane in any apparent danger, Mrs. Bennet would have been very miserable; but being satisfied on seeing her that her illness was not alarming, she had no wish of her recovering immediately, as her restoration to health would probably remove her from Netherfield. She would not listen, therefore, to her daughter's proposal of being carried home; neither did the apothecary, who arrived about the same time, think it at all advisable. After sitting a little with Jane, on Miss Bingley's appearance and invitation, the mother and three daughters all attended her into the breakfast parlor. Bingley met them with hopes that Mrs. Bennet had not found Miss Bennet worse than she expected.

"Indeed I have, Sir," was her answer. "She is a great deal too ill to be moved. Mr. Jones says we must not think of moving her. We must trespass a little longer on your kindness."

"Removed!" cried Bingley. "It must not be thought of. My sister, I am sure, will not hear of her removal."

# Importance Criteria

A float score between 0-10 that represents the relevance of the text to literary analysis, historical context, thematic interpretation, and cultural significance, with 1 being trivial or irrelevant and 10 being highly significant, profound, and impactful to the understanding of the text and its implications.
#############################

### Example 3

# Domain

Environmental Science

# Persona

You are an environmental scientist with a focus on climate change and sustainability. You are skilled at analyzing data, interpreting social commentary and recommending policy changes. You are adept at helping people understand the causes and consequences of climate change, providing insights into how they can reduce their carbon footprint, adopt sustainable practices, and contribute to a healthier planet.

# Data

Host 1 (Anna): Welcome to "Green Living Today," the podcast where we explore practical tips and inspiring stories about sustainable living. I'm your host, Anna Green.

Host 2 (Mark): And I'm Mark Smith. Today, we have a special episode focused on reducing plastic waste in our daily lives. We'll be talking to a special guest who has made significant strides in living a plastic-free lifestyle.

Anna: That's right, Mark. Our guest today is Laura Thompson, the founder of "Plastic-Free Living," a blog dedicated to sharing tips and resources for reducing plastic use. Welcome to the show, Laura!

Guest (Laura): Thanks, Anna and Mark. It's great to be here.

Mark: Laura, let's start by talking about your journey. What inspired you to start living a plastic-free lifestyle?

# Importance Criteria

A float score between 0-10 that represents the relevance of the text to sustainability, plastic waste reduction, and environmental policies, with 1 being trivial or irrelevant and 10 being highly significant, impactful, and actionable in promoting environmental awareness.
#############################


#############################
-Real Data-
#############################

# Domain

{domain}

# Persona

{persona}

# Data

{input_text}

# Importance Criteria


"""
