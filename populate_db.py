import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from sqlalchemy import delete, select, update

import models
from database import AsyncSessionLocal, engine
from image_process_utils import PROFILE_PICS_DIR
from main import app

POPULATE_IMAGES_DIR = Path("populate_images")


USERS = [
    {
        "username": "alexmorgan",
        "email": "alex.morgan@example.com",
        "password": "PortfolioDemo1!",
        "image": "kazi.png",
    },
    {
        "username": "jamielee",
        "email": "jamie.lee@example.com",
        "password": "PortfolioDemo2!",
        # No image - uses default
    },
    {
        "username": "sarahchen",
        "email": "sarah.chen@example.com",
        "password": "PortfolioDemo3!",
        "image": "willow.png",
    },
    {
        "username": "michaelreed",
        "email": "michael.reed@example.com",
        "password": "PortfolioDemo4!",
        "image": "farmdogs.png",
    },
    {
        "username": "nataliepark",
        "email": "natalie.park@example.com",
        "password": "PortfolioDemo5!",
        "image": "poppy.png",
    },
    {
        "username": "danielbrooks",
        "email": "daniel.brooks@example.com",
        "password": "PortfolioDemo6!",
        "image": "bronx.png",
    },
]


POSTS = [
    {
        "title": "The Project That Finally Made Backend Development Click",
        "content": (
            "For a long time, backend development felt like a collection of unrelated "
            "concepts: databases, authentication, APIs, validation, deployment. That "
            "changed when I built a project from scratch instead of following a tutorial. "
            "Having to make every architectural decision myself forced me to understand "
            "how the pieces actually fit together. I still have plenty to learn, but "
            "building something end to end made the difference."
        ),
    },
    {
        "title": "What I Learned From Rebuilding My Portfolio",
        "content": (
            "I originally thought rebuilding my portfolio would mostly be a frontend "
            "exercise. It turned into a lesson in everything else. I had to think about "
            "authentication, database structure, image uploads, error handling, responsive "
            "design, and deployment. The biggest lesson was that a portfolio isn't just "
            "about showing finished projects. It should show how you think."
        ),
    },
    {
        "title": "A Small Refactor That Made a Huge Difference",
        "content": (
            "I spent an afternoon cleaning up a service that had slowly grown into one "
            "large file. Nothing was technically broken, but every change felt risky. "
            "I separated the database operations, authentication logic, and request "
            "handling into smaller pieces. The application didn't look dramatically "
            "different afterward, but working on it became much easier. Sometimes the "
            "best refactors are the ones that make future work boring."
        ),
    },
    {
        "title": "Why I Started Writing About the Things I Build",
        "content": (
            "I've always been better at understanding something after explaining it to "
            "someone else. Writing short posts about projects has become an extension "
            "of that habit. It forces me to slow down, figure out what I actually "
            "understand, and document the decisions I made. It also gives me something "
            "more useful than a list of technologies when I'm looking back at old work."
        ),
    },
    {
        "title": "Getting Comfortable With SQL Took Longer Than Expected",
        "content": (
            "I initially tried to hide behind an ORM and avoid learning much SQL. That "
            "worked until I started debugging queries that weren't doing what I expected. "
            "Learning joins, indexes, transactions, and query plans completely changed "
            "how I think about database code. I still appreciate the convenience of an "
            "ORM, but understanding the SQL underneath it makes the abstraction much more "
            "useful."
        ),
    },
    {
        "title": "The Difference Between a Demo and a Real Application",
        "content": (
            "A demo can get away with hardcoded data, minimal error handling, and a single "
            "happy path. A real application can't. Once I started treating my personal "
            "projects like software someone else might actually use, I began paying much "
            "more attention to authentication, validation, loading states, failures, "
            "logging, and deployment. Those details aren't as exciting as adding features, "
            "but they're what make a project feel finished."
        ),
    },
    {
        "title": "My Favorite Way to Learn a New Framework",
        "content": (
            "I usually spend the first hour reading documentation and the next few hours "
            "trying to build something ridiculously small. A notes API, a URL shortener, "
            "or a simple authentication service is enough. Once I hit a problem that "
            "actually matters to the project, the documentation becomes much easier to "
            "understand. I learn more from one small broken project than I do from hours "
            "of passively watching tutorials."
        ),
    },
    {
        "title": "When Overengineering Finally Bit Me",
        "content": (
            "I once spent more time designing an architecture than I spent building the "
            "feature. There were abstractions for things that only had one implementation, "
            "interfaces that didn't solve a real problem, and layers that mostly forwarded "
            "arguments. It looked sophisticated and made simple changes harder. These days "
            "I try to earn complexity instead of adding it because I think I might need it "
            "later."
        ),
    },
    {
        "title": "A Better Approach to Environment Variables",
        "content": (
            "Environment variables started as something I used because every tutorial told "
            "me to. Eventually I understood why they matter. Database credentials, secret "
            "keys, API tokens, and environment-specific configuration shouldn't be baked "
            "into the application. Keeping configuration outside the code also makes it "
            "much easier to move the same application between local development, staging, "
            "and production."
        ),
    },
    {
        "title": "The First Time I Had to Debug a Production Issue",
        "content": (
            "Nothing makes logging suddenly seem important like trying to figure out why "
            "something broke when you can't reproduce it locally. My first instinct was "
            "to add print statements everywhere. Eventually I learned to think about what "
            "information would actually help me reconstruct what happened. Good logs aren't "
            "about logging everything. They're about leaving useful clues for your future self."
        ),
    },
    {
        "title": "Why I Prefer Boring APIs",
        "content": (
            "The best APIs I've worked with aren't clever. Their endpoints are predictable, "
            "their responses are consistent, and their errors make sense. There is something "
            "really satisfying about looking at an unfamiliar API and immediately knowing "
            "how to use it. Fancy architecture can be useful, but predictability is usually "
            "more valuable to the person consuming your software."
        ),
    },
    {
        "title": "A Weekend Project That Got Out of Hand",
        "content": (
            "The plan was simple: spend Saturday building a tiny application to practice "
            "authentication. By Sunday evening I had added image uploads, pagination, "
            "password resets, database migrations, and a completely unnecessary dark mode. "
            "It wasn't exactly what I planned to build, but those accidental features taught "
            "me more than the original project idea. Apparently I have no concept of scope."
        ),
    },
    {
        "title": "What Makes a Good Developer Experience?",
        "content": (
            "Small conveniences add up. Fast tests, useful error messages, predictable "
            "project structure, automatic formatting, good documentation, and a simple "
            "local setup can make a codebase dramatically nicer to work in. Developer "
            "experience isn't something you notice when it's good. You notice it when "
            "everything takes five unnecessary steps."
        ),
    },
    {
        "title": "Learning to Read Documentation Properly",
        "content": (
            "I used to search for tutorials every time I got stuck. Eventually I realized "
            "I was often looking for information that was already in the official docs. "
            "The trick was learning how to read them. Examples tell you how something works, "
            "but the reference documentation tells you what the software actually promises "
            "to do. That distinction has saved me a lot of time."
        ),
    },
    {
        "title": "The Little Things That Make a Login Page Feel Finished",
        "content": (
            "A login form is easy to build. A good login experience takes more thought. "
            "What happens when the password is wrong? What if the request takes a few seconds? "
            "Can the user see that their action worked? What happens after a session expires? "
            "I've started paying much more attention to these small interactions because they "
            "are often what separates a working feature from a polished one."
        ),
    },
    {
        "title": "Why Pagination Is More Important Than It Looks",
        "content": (
            "Pagination seemed like one of those features I could add later. Then I built "
            "a page that loaded every record from the database and immediately understood "
            "why it matters. A handful of records is fine. Thousands are a completely "
            "different story. Pagination isn't just a UI feature; it's part of designing "
            "an application that can grow without quietly becoming expensive."
        ),
    },
    {
        "title": "What I Look For in a Good Database Schema",
        "content": (
            "When designing a schema, I try to imagine what the application will need to "
            "ask the database rather than just thinking about what data exists. Relationships, "
            "constraints, indexes, and uniqueness rules all become much clearer when you "
            "start from actual queries. A schema isn't just a place to store information. "
            "It's part of the application's architecture."
        ),
    },
    {
        "title": "The Most Useful Git Habit I Picked Up",
        "content": (
            "I used to make enormous commits with messages like 'finished project' or "
            "'fix stuff.' Now I try to keep commits focused on one logical change. It makes "
            "reviewing history much easier and gives me a way to understand why something "
            "changed months later. It sounds minor, but good commit history has saved me "
            "more than once."
        ),
    },
    {
        "title": "Building Features Around Real User Actions",
        "content": (
            "One mistake I made early on was designing features around database models "
            "instead of user actions. Users don't think in terms of CRUD operations. They "
            "think 'I want to save this,' 'I want to update my profile,' or 'I forgot my "
            "password.' Starting from those actions leads to much better decisions about "
            "validation, permissions, and the overall interface."
        ),
    },
    {
        "title": "Why Error Messages Are Part of the UI",
        "content": (
            "An error response might technically belong to the backend, but the person "
            "experiencing it doesn't care which layer produced it. A vague 'Something went "
            "wrong' message leaves users stuck. A useful error tells them what happened "
            "and, when possible, what they can do next. I've started treating error messages "
            "as part of the user experience rather than an afterthought."
        ),
    },
    {
        "title": "The Joy of Finally Understanding Async Code",
        "content": (
            "Async programming was one of those topics that made sense in theory and felt "
            "strange in practice. The turning point was realizing that async isn't about "
            "making everything faster. It's about allowing a program to do useful work "
            "while waiting on things like network or database operations. Once that clicked, "
            "the syntax stopped feeling magical and started feeling practical."
        ),
    },
    {
        "title": "What I Learned From Building Image Uploads",
        "content": (
            "Image uploads look simple from the outside. Behind the scenes there are file "
            "types, file sizes, storage locations, naming collisions, validation, cleanup, "
            "and security concerns to think about. Building the feature forced me to consider "
            "all of those edge cases. It's a good reminder that seemingly small features "
            "often have much more depth than their UI suggests."
        ),
    },
    {
        "title": "My Approach to Authentication",
        "content": (
            "Authentication is one area where I don't want to reinvent anything unnecessarily. "
            "I prefer using established libraries and patterns, keeping password handling "
            "simple, storing secrets outside the repository, and making authorization rules "
            "explicit. Security isn't a place where clever code earns extra points. Boring "
            "and well-understood is usually exactly what I want."
        ),
    },
    {
        "title": "The Best Debugging Tool Is Still Asking Why",
        "content": (
            "When something breaks, it's tempting to immediately change the line that looks "
            "wrong. I've gotten better results by asking why the behavior happened in the "
            "first place. Why is this value empty? Why did this query return nothing? Why "
            "did this request get here? Following the chain back to the original assumption "
            "usually produces a better fix than patching the symptom."
        ),
    },
    {
        "title": "A Few Things I Wish I Knew Before My First API",
        "content": (
            "I wish I'd understood earlier that API design is mostly about consistency. "
            "Consistent naming, status codes, validation, authentication, and response "
            "formats make everything easier. I also wish I'd started thinking about error "
            "cases earlier. The happy path is usually easy. The interesting engineering "
            "starts when things go wrong."
        ),
    },
    {
        "title": "Why I Still Like Building Things From Scratch",
        "content": (
            "There are plenty of tools that can generate a project in minutes, and they are "
            "great. But sometimes I deliberately build something without a starter template. "
            "Starting with an empty directory forces me to make decisions that a template "
            "normally makes for me. It is slower, but it has taught me a lot about what "
            "actually belongs in a project."
        ),
    },
    {
        "title": "How I Keep Personal Projects From Becoming Abandoned",
        "content": (
            "The easiest way for me to abandon a project is to make the first version too "
            "ambitious. Now I try to define one small version that I could realistically "
            "finish in a weekend. Once that works, adding features becomes fun instead of "
            "overwhelming. A small finished project teaches me more than a massive project "
            "that stays at 60 percent forever."
        ),
    },
    {
        "title": "The Difference Between Knowing a Tool and Understanding It",
        "content": (
            "I can use a library without really understanding it. That's useful, but there's "
            "a point where understanding the underlying idea makes everything easier. "
            "Learning what a database transaction actually does, for example, makes ORM "
            "behavior much less mysterious. I'm trying to spend more time learning the "
            "concepts behind my tools instead of memorizing their APIs."
        ),
    },
    {
        "title": "A Simple Rule for Choosing Dependencies",
        "content": (
            "Every dependency adds convenience, but it also adds something I have to maintain. "
            "Before adding a package, I try to ask whether it solves a real problem and whether "
            "the problem is large enough to justify another dependency. Sometimes the answer "
            "is absolutely yes. Other times, a few straightforward lines of code are easier "
            "to understand and maintain."
        ),
    },
    {
        "title": "What I Like About Python",
        "content": (
            "The biggest reason I keep coming back to Python isn't one particular feature. "
            "It's how quickly I can go from an idea to something working. The ecosystem is "
            "huge, the syntax stays out of the way, and there are mature tools for almost "
            "everything I tend to build. It makes experimentation feel cheap, which is "
            "exactly what I want when I'm learning."
        ),
    },
    {
        "title": "Trying to Make My Code Easier to Delete",
        "content": (
            "One of the stranger lessons I've learned is that good code isn't necessarily "
            "code that will exist forever. Requirements change. Libraries get replaced. "
            "Features get removed. I try to keep boundaries clear enough that deleting or "
            "replacing a piece of the application doesn't require rewriting everything "
            "around it. Sometimes maintainability is really just making change less painful."
        ),
    },
    {
        "title": "What I Learned From a Failed Deployment",
        "content": (
            "The application worked perfectly on my machine, right up until I deployed it. "
            "A missing environment variable and an incorrect database configuration later, "
            "I had a much better appreciation for deployment parity. Since then, I try to "
            "make the deployment process as repeatable as possible and document the things "
            "the application actually needs to run."
        ),
    },
    {
        "title": "Why I Started Paying Attention to Accessibility",
        "content": (
            "Accessibility used to feel like something I would get to after the main features "
            "were finished. Now I try to consider it while building. Keyboard navigation, "
            "labels, readable contrast, meaningful buttons, and sensible focus behavior "
            "aren't just accessibility improvements. They usually make the interface better "
            "for everyone."
        ),
    },
    {
        "title": "The Most Useful Feature Nobody Notices",
        "content": (
            "Loading states are easy to overlook because, when they work, users barely notice "
            "them. But a button that gives no indication after being clicked makes an application "
            "feel broken. The same goes for empty states and useful feedback after an action. "
            "These aren't flashy features, but they make software feel responsive and intentional."
        ),
    },
    {
        "title": "How I Decide What to Build Next",
        "content": (
            "When a project starts getting bigger, I keep a list of possible improvements and "
            "sort them into three categories: things users actually need, things that will teach "
            "me something, and things that just sound fun. The best tasks usually overlap two "
            "of those categories. It keeps me from spending a week polishing something nobody "
            "will ever use."
        ),
    },
    {
        "title": "A Better Way to Think About Testing",
        "content": (
            "I used to think testing meant trying to prove that the application worked. Now I "
            "think of it more as defining what I expect the application to do. That shift makes "
            "tests much easier to write. Instead of testing every implementation detail, I focus "
            "on the behavior that matters: valid requests work, invalid requests fail correctly, "
            "and important business rules stay intact."
        ),
    },
    {
        "title": "Why Good Naming Is Worth the Extra Minute",
        "content": (
            "I've opened old code and spent more time figuring out what a variable meant than "
            "I would have spent writing the feature again. Naming isn't glamorous, but good "
            "names remove entire paragraphs of explanation. If a function needs a long comment "
            "to explain what its name should have said, I usually take that as a sign that "
            "the name needs another pass."
        ),
    },
    {
        "title": "The Problem With Always Chasing New Technology",
        "content": (
            "There is always a new framework, database, runtime, or tool promising to change "
            "everything. I enjoy trying new technology, but I've realized that constantly "
            "switching stacks can become a form of procrastination. Sometimes the most useful "
            "thing I can do is take the tools I already know and build something substantial "
            "with them."
        ),
    },
    {
        "title": "What Makes a Project Portfolio-Worthy?",
        "content": (
            "A project doesn't need to be revolutionary to be worth showing. I think a strong "
            "portfolio project demonstrates that you can take a problem, make reasonable "
            "technical decisions, build the thing, handle edge cases, and explain what you "
            "learned. A simple application with thoughtful engineering is much more interesting "
            "to me than a huge project where the technology is doing all the talking."
        ),
    },
    {
        "title": "Taking a Break Actually Helped Me Solve the Problem",
        "content": (
            "I spent almost two hours staring at a bug that turned out to be caused by one "
            "incorrect assumption. I stepped away, made dinner, came back, and spotted it "
            "within five minutes. Sometimes the best debugging strategy isn't another tool "
            "or another search. It's giving your brain enough distance to see the problem "
            "without staring directly at it."
        ),
    },
    {
        "title": "Things I Want to Get Better At This Year",
        "content": (
            "I'm trying to focus less on collecting technologies and more on improving the "
            "fundamentals. Better database design, cleaner architecture, stronger testing, "
            "more thoughtful UI decisions, and a deeper understanding of deployment are all "
            "high on the list. I'd rather become significantly better at a handful of useful "
            "skills than have ten frameworks listed on my resume that I barely remember using."
        ),
    },
    {
        "title": "Building Software Is Mostly Making Decisions",
        "content": (
            "The more I build, the less I think programming is about typing code. Most of the "
            "interesting work happens before the code exists: deciding what belongs in the "
            "database, where validation should happen, how permissions work, what happens when "
            "a request fails, and which parts should stay independent. Writing the code is "
            "important, but making good decisions is where most of the engineering happens."
        ),
    },
    {
        "title": "The Projects I Remember Most Aren't the Biggest Ones",
        "content": (
            "Some of my favorite projects started as tiny experiments. A weekend app, a script "
            "to automate something annoying, or a small API built just to understand a concept. "
            "They weren't impressive on paper, but each one solved a real problem or taught me "
            "something I didn't know before. That's probably why I enjoy personal projects so "
            "much: there is always another reason to build something."
        ),
    },
]


# The 44th post - always the oldest.
POST_44 = {
    "title": "A Note From the Beginning",
    "content": (
        "If you made it all the way to the oldest post on the site, thanks for looking around. "
        "This project started as a simple idea to learn more about building a full-stack "
        "application, but it slowly became a place to document the things I was learning along "
        "the way. There are better ways to build almost everything here, and that's kind of "
        "the point. Projects are snapshots of where you are in your learning journey."
    ),
}


async def clear_existing_data() -> None:
    # Delete profile pictures from local storage
    if PROFILE_PICS_DIR.exists():
        for file in PROFILE_PICS_DIR.iterdir():
            if file.is_file() and file.name != ".gitkeep":
                file.unlink()
        print(f"Deleted profile pictures from {PROFILE_PICS_DIR}")

    # Clear database tables (order respects foreign keys)
    async with AsyncSessionLocal() as db:
        await db.execute(delete(models.PasswordResetToken))
        await db.execute(delete(models.Post))
        await db.execute(delete(models.User))
        await db.commit()

    print("Cleared existing data")


async def update_post_dates() -> None:
    now = datetime.now(UTC)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(models.Post).order_by(models.Post.id))
        posts = result.scalars().all()

        if not posts:
            return

        # First post (POST_44) is the oldest.
        await db.execute(
            update(models.Post)
            .where(models.Post.id == posts[0].id)
            .values(date_posted=now - timedelta(days=90)),
        )

        # Remaining posts become progressively newer.
        for i, post in enumerate(posts[1:], start=1):
            days_ago = (len(posts) - i) * 1.5
            hours_offset = (i * 7) % 24

            post_date = now - timedelta(
                days=ago if False else days_ago,
                hours=hours_offset,
            )

            await db.execute(
                update(models.Post)
                .where(models.Post.id == post.id)
                .values(date_posted=post_date),
            )

        await db.commit()

    print("Updated post dates")


async def populate() -> None:
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://localhost",
    ) as client:
        await clear_existing_data()

        users: list[dict] = []

        print(f"\nCreating {len(USERS)} users...")

        for user_data in USERS:
            response = await client.post(
                "/api/users",
                json={
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "password": user_data["password"],
                },
            )
            response.raise_for_status()

            user = response.json()
            print(f"  Created: {user['username']}")

            response = await client.post(
                "/api/users/token",
                data={
                    "username": user_data["email"],
                    "password": user_data["password"],
                },
            )
            response.raise_for_status()

            token = response.json()["access_token"]

            if image_name := user_data.get("image"):
                image_path = POPULATE_IMAGES_DIR / image_name

                if image_path.exists():
                    response = await client.patch(
                        f"/api/users/{user['id']}/picture",
                        files={
                            "file": (
                                image_name,
                                image_path.read_bytes(),
                                "image/png",
                            ),
                        },
                        headers={
                            "Authorization": f"Bearer {token}",
                        },
                    )
                    response.raise_for_status()
                    print(f"    Uploaded: {image_name}")

            users.append(
                {
                    "id": user["id"],
                    "username": user["username"],
                    "token": token,
                },
            )

        print(f"\nCreating {len(POSTS) + 1} posts...")

        # Create the oldest post first.
        response = await client.post(
            "/api/posts",
            json={
                "title": POST_44["title"],
                "content": POST_44["content"],
            },
            headers={
                "Authorization": f"Bearer {users[0]['token']}",
            },
        )
        response.raise_for_status()

        print(f"  Created: '{POST_44['title']}'")

        # Create remaining posts in reverse so the newest posts are created last.
        for i, post_data in enumerate(reversed(POSTS)):
            user = users[i % len(users)]

            response = await client.post(
                "/api/posts",
                json={
                    "title": post_data["title"],
                    "content": post_data["content"],
                },
                headers={
                    "Authorization": f"Bearer {user['token']}",
                },
            )
            response.raise_for_status()

            title = post_data["title"]

            if len(title) > 50:
                print(f"  Created: '{title[:50]}...'")
            else:
                print(f"  Created: '{title}'")

        print("\nUpdating post dates...")
        await update_post_dates()

    await engine.dispose()

    print("\nDone!")
    print(f"  {len(USERS)} users")
    print(f"  {len(POSTS) + 1} posts")
    print("  Profile pictures saved locally")


if __name__ == "__main__":
    if __import__("sys").platform == "win32":
        asyncio.run(
            populate(),
            loop_factory=lambda: asyncio.SelectorEventLoop(),
        )
    else:
        asyncio.run(populate())