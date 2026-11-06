"""Safe simulated terminal: explicit allowlist + in-memory synthetic filesystem.

No subprocess, os.system, eval, exec, network sockets, or real filesystem access
is used. Commands operate only on scenario data loaded from the database.
"""
import re
import shlex
from app.helpers import utc_now, safe_key, normalize_answer
from app.errors import NotFoundError, ValidationError, ConflictError
from app.service_scoring import score_question
from app.service_activity import ActivityService

ALLOWED_COMMANDS = {"help", "pwd", "ls", "cd", "cat", "head", "tail", "grep", "wc",
                    "find", "stat", "whoami", "uname", "hostname", "ip", "ps",
                    "netstat", "history", "clear", "echo", "file", "sort", "uniq"}
PIPEABLE = {"grep", "wc", "head", "tail", "sort", "uniq"}
MAX_OUTPUT = 20000


class LaboratoryService:
    def __init__(self, repository, content):
        self.repo = repository
        self.content = content
        self.activity = ActivityService(repository)

    async def list_scenarios(self) -> list[dict]:
        rows = await self.content.list_collection("laboratory")
        return [{k: s[k] for k in ("id", "title", "description", "difficulty", "objectives", "order") if k in s}
                for s in rows]

    async def get_scenario(self, scenario_id: str) -> dict:
        scenario = await self.content.get_item("laboratory", scenario_id)
        return {k: v for k, v in scenario.items() if k != "exercises"} | {
            "exercises": [{"id": e["id"], "title": e["title"], "instructions": e["instructions"],
                           "hints": e.get("hints", [])} for e in scenario.get("exercises", [])]}

    async def session(self, uid: str, scenario_id: str) -> dict:
        scenario = await self.content.get_item("laboratory", scenario_id)
        path = f"lab_sessions/{safe_key(uid)}/{safe_key(scenario_id)}"
        session = await self.repo.get(path)
        if not session:
            session = {"scenario_id": scenario_id, "uid": uid, "cwd": scenario.get("start_dir", "/home/analyst"),
                       "history": [], "completed_exercises": [], "created_at": utc_now()}
            await self.repo.set(path, session)
        return session

    @staticmethod
    def _resolve(cwd: str, target: str) -> str:
        if not target or target == "~":
            return "/home/analyst"
        base = target if target.startswith("/") else f"{cwd.rstrip('/')}/{target}"
        parts = []
        for part in base.split("/"):
            if part in ("", "."):
                continue
            if part == "..":
                if parts:
                    parts.pop()
            else:
                parts.append(part)
        return "/" + "/".join(parts)

    @staticmethod
    def _node(fs: dict, path: str):
        return fs.get(path)

    def _list_dir(self, fs: dict, path: str, long=False, all_=False) -> str:
        children = set()
        prefix = path.rstrip("/") + "/"
        for p in fs:
            if p.startswith(prefix):
                rest = p[len(prefix):]
                if rest:
                    children.add(rest.split("/")[0])
        names = sorted(children)
        if not all_:
            names = [n for n in names if not n.startswith(".")]
        if not long:
            return "\n".join(names)
        lines = []
        for name in names:
            child = self._resolve(path, name)
            node = fs.get(child, {"type": "dir"})
            if node.get("type") == "dir" or child not in fs:
                lines.append(f"drwxr-xr-x 1 analyst analyst 4096 Jan 10 09:00 {name}")
            else:
                size = len(node.get("content", "").encode())
                lines.append(f"-rw-r--r-- 1 analyst analyst {size} Jan 10 09:00 {name}")
        return "\n".join(lines)

    def execute(self, scenario: dict, session: dict, command_line: str) -> dict:
        if len(command_line) > 1000:
            raise ValidationError("الأمر طويل جداً")
        if any(ch in command_line for ch in [";", "&&", "||", "`", "$(", ">", "<", "\n", "\r"]):
            raise ValidationError("المختبر يمنع التسلسل وإعادة التوجيه واستبدال الأوامر")
        stages = [s.strip() for s in command_line.split("|")]
        if len(stages) > 4:
            raise ValidationError("يسمح بأربع مراحل كحد أقصى")
        parsed = []
        for stage in stages:
            try:
                tokens = shlex.split(stage)
            except ValueError as exc:
                raise ValidationError("صيغة الأمر غير صالحة؛ تحقق من علامات الاقتباس") from exc
            if not tokens:
                raise ValidationError("اكتب أمراً")
            cmd = tokens[0]
            if cmd not in ALLOWED_COMMANDS:
                raise ValidationError(f"الأمر {cmd} غير مسموح في المحاكاة. اكتب help")
            if len(stages) > 1 and cmd not in PIPEABLE and cmd != "cat" and cmd != "ls":
                raise ValidationError("هذا الأمر لا يدعم الأنبوب في المحاكاة")
            parsed.append((cmd, tokens[1:]))
        fs = scenario["filesystem"]
        cwd = session["cwd"]
        stdin = None
        output = ""
        explanation = ""
        new_cwd = cwd
        clear = False
        for index, (cmd, args) in enumerate(parsed):
            text, explanation, new_cwd, clear = self._run_command(
                cmd, args, fs, new_cwd, stdin, scenario)
            stdin = text
            output = text
        output = output[:MAX_OUTPUT]
        entry = {"command": command_line, "output": output, "explanation": explanation,
                 "cwd": new_cwd, "at": utc_now(), "simulated": True}
        return entry

    def _run_command(self, cmd, args, fs, cwd, stdin, scenario):
        explanation = ""
        new_cwd = cwd
        clear = False
        def need_file(target):
            path = self._resolve(cwd, target)
            node = fs.get(path)
            if not node or node.get("type") != "file":
                raise ValidationError(f"الملف غير موجود في المحاكاة: {target}")
            return path, node
        if cmd == "help":
            text = "الأوامر المتاحة: " + ", ".join(sorted(ALLOWED_COMMANDS))
            explanation = "هذه أوامر محاكاة تعمل على ملفات اصطناعية فقط ولا تمس جهازك."
        elif cmd == "pwd":
            text = cwd
            explanation = "pwd يعرض مسار دليل العمل الحالي داخل نظام الملفات الوهمي."
        elif cmd == "whoami":
            text = scenario.get("user", "analyst")
            explanation = "whoami يعرض هوية المستخدم في السيناريو الاصطناعي."
        elif cmd == "uname":
            text = "Linux cyberlife-lab 6.1.0-training x86_64 GNU/Linux" if "-a" in args else "Linux"
            explanation = "uname يعرض معلومات نواة النظام التدريبية، وليس نظام جهازك الحقيقي."
        elif cmd == "hostname":
            text = scenario.get("hostname", "soc-workstation")
            explanation = "hostname يعرض اسم الجهاز الافتراضي في السيناريو."
        elif cmd == "ip":
            text = scenario.get("network", "1: lo: <LOOPBACK> inet 127.0.0.1/8\n2: eth0: <UP> inet 10.10.20.15/24")
            explanation = "ip addr يعرض واجهات الشبكة الافتراضية؛ العناوين هنا للتدريب فقط."
        elif cmd == "ps":
            text = scenario.get("processes", "PID USER COMMAND\n118 analyst python3 training_agent.py")
            explanation = "ps يعرض عمليات اصطناعية لممارسة قراءة قائمة العمليات."
        elif cmd == "netstat":
            text = scenario.get("connections", "Proto Local Foreign State\nTCP 10.10.20.15:49152 10.10.20.10:443 ESTABLISHED")
            explanation = "netstat يعرض اتصالات وهمية؛ لا يوجد فحص شبكي حقيقي."
        elif cmd == "history":
            text = ""
            explanation = "history يعرض أوامر الجلسة؛ يُحدّث من السجل المخزن."
        elif cmd == "clear":
            text = ""
            clear = True
            explanation = "clear يمسح شاشة الطرفية فقط ولا يحذف السجل المخزن."
        elif cmd == "echo":
            text = " ".join(args)
            explanation = "echo يطبع النص كما هو؛ لا ينفذ أي أوامر داخل النص."
        elif cmd == "ls":
            long = any(a in args for a in ("-l", "-la", "-al", "-l-a"))
            all_ = any(a in args for a in ("-a", "-la", "-al"))
            targets = [a for a in args if not a.startswith("-")]
            path = self._resolve(cwd, targets[0] if targets else ".")
            node = fs.get(path)
            if node and node.get("type") == "file":
                text = path.rsplit("/", 1)[-1]
            else:
                text = self._list_dir(fs, path, long, all_)
            explanation = "ls يسرد محتويات الدليل. -l للتفاصيل، -a يشمل الملفات المخفية التي تبدأ بنقطة."
        elif cmd == "cd":
            target = args[0] if args else "~"
            path = self._resolve(cwd, target)
            if path != "/" and path not in fs and not any(p.startswith(path + "/") for p in fs):
                raise ValidationError(f"الدليل غير موجود: {target}")
            node = fs.get(path)
            if node and node.get("type") == "file":
                raise ValidationError("لا يمكن الدخول إلى ملف كأنه دليل")
            new_cwd = path
            text = ""
            explanation = "cd يغيّر دليل العمل داخل المحاكاة فقط."
        elif cmd == "cat":
            if stdin is not None and not args:
                text = stdin
            else:
                if not args:
                    raise ValidationError("cat يحتاج اسم ملف")
                parts = []
                for target in args:
                    _, node = need_file(target)
                    parts.append(node.get("content", ""))
                text = "\n".join(parts)
            explanation = "cat يعرض محتوى ملف اصطناعي كاملاً؛ استخدم head للسجلات الكبيرة."
        elif cmd in {"head", "tail"}:
            n = 10
            if "-n" in args:
                i = args.index("-n")
                if i + 1 >= len(args) or not args[i+1].isdigit():
                    raise ValidationError("head/tail يحتاج عدداً بعد -n")
                n = min(int(args[i+1]), 500)
                args = args[:i] + args[i+2:]
            if args:
                _, node = need_file(args[0])
                content = node.get("content", "")
            else:
                content = stdin or ""
            lines = content.splitlines()
            text = "\n".join(lines[:n] if cmd == "head" else lines[-n:])
            explanation = f"{cmd} يعرض أول/آخر {n} أسطر دون تعديل الملف."
        elif cmd == "grep":
            if not args:
                raise ValidationError("grep يحتاج نمط بحث")
            ignore = "-i" in args
            invert = "-v" in args
            count = "-c" in args
            positional = [a for a in args if not a.startswith("-")]
            pattern = positional[0]
            try:
                regex = re.compile(pattern, re.IGNORECASE if ignore else 0)
            except re.error as exc:
                raise ValidationError("نمط البحث غير صالح") from exc
            if len(positional) > 1:
                _, node = need_file(positional[1])
                content = node.get("content", "")
            else:
                content = stdin or ""
            matched = [line for line in content.splitlines() if bool(regex.search(line)) != invert]
            text = str(len(matched)) if count else "\n".join(matched)
            explanation = "grep يرشح الأسطر المطابقة لنمط نصي. -i يتجاهل حالة الأحرف، -v يعكس المطابقة، -c يعدّ."
        elif cmd == "wc":
            content = stdin or ""
            if args and not args[0].startswith("-"):
                _, node = need_file(args[0])
                content = node.get("content", "")
            lines = content.splitlines()
            if "-l" in args:
                text = str(len(lines))
            elif "-w" in args:
                text = str(len(content.split()))
            else:
                text = f"{len(lines)} {len(content.split())} {len(content.encode())}"
            explanation = "wc يعدّ الأسطر أو الكلمات أو البايتات؛ -l لعدد الأسطر فقط."
        elif cmd == "find":
            start = self._resolve(cwd, args[0] if args and not args[0].startswith("-") else ".")
            name = None
            if "-name" in args:
                i = args.index("-name")
                if i + 1 >= len(args):
                    raise ValidationError("find -name يحتاج نمطاً")
                name = args[i+1].replace("*", ".*").replace("?", ".")
            rows = []
            for path in sorted(fs):
                if path == start or path.startswith(start.rstrip("/") + "/"):
                    if name is None or re.fullmatch(name, path.rsplit("/", 1)[-1]):
                        rows.append(path)
            text = "\n".join(rows)
            explanation = "find يبحث في شجرة الملفات الوهمية بالاسم أو المسار."
        elif cmd == "stat":
            if not args:
                raise ValidationError("stat يحتاج مساراً")
            path, node = need_file(args[0])
            size = len(node.get("content", "").encode())
            text = f"File: {path}\nSize: {size}\nType: regular file\nOwner: analyst\nModify: 2026-01-10 09:00:00"
            explanation = "stat يعرض بيانات وصفية للملف مثل الحجم والمالك ووقت التعديل التدريبية."
        elif cmd == "file":
            if not args:
                raise ValidationError("file يحتاج مساراً")
            _, node = need_file(args[0])
            text = node.get("file_type", "ASCII text")
            explanation = "file يصف نوع الملف بناءً على بيانات السيناريو، وليس فحصاً ثنائياً حقيقياً."
        elif cmd == "sort":
            content = stdin or ""
            if args and not args[0].startswith("-"):
                _, node = need_file(args[0])
                content = node.get("content", "")
            lines = content.splitlines()
            text = "\n".join(sorted(lines, reverse="-r" in args))
            explanation = "sort يرتب الأسطر نصياً؛ -r يعكس الترتيب."
        elif cmd == "uniq":
            content = stdin or ""
            if args and not args[0].startswith("-"):
                _, node = need_file(args[0])
                content = node.get("content", "")
            lines = content.splitlines()
            out = []
            counts = []
            for line in lines:
                if out and out[-1] == line:
                    counts[-1] += 1
                else:
                    out.append(line)
                    counts.append(1)
            if "-c" in args:
                text = "\n".join(f"{c} {l}" for c, l in zip(counts, out))
            else:
                text = "\n".join(out)
            explanation = "uniq يزيل التكرار المتجاور؛ غالباً يسبقه sort. -c يعرض عدد التكرارات."
        else:
            raise ValidationError("أمر غير مدعوم")
        return text, explanation, new_cwd, clear

    async def run_command(self, uid: str, scenario_id: str, command_line: str) -> dict:
        scenario = await self.content.get_item("laboratory", scenario_id)
        session = await self.session(uid, scenario_id)
        entry = self.execute(scenario, session, command_line)
        if entry["command"].split()[0] == "history":
            entry["output"] = "\n".join(f"{i+1} {h['command']}" for i, h in enumerate(session["history"][-50:]))
        def append(current):
            rows = current if isinstance(current, list) else []
            return (rows + [entry])[-100:]
        await self.repo.transaction(f"lab_sessions/{safe_key(uid)}/{safe_key(scenario_id)}/history", append)
        await self.repo.update(f"lab_sessions/{safe_key(uid)}/{safe_key(scenario_id)}",
                               {"cwd": entry["cwd"], "last_command_at": utc_now()})
        return entry

    async def validate_exercise(self, uid: str, scenario_id: str, payload) -> dict:
        scenario = await self.content.get_item("laboratory", scenario_id)
        exercise = next((e for e in scenario.get("exercises", []) if e["id"] == payload.exercise_id), None)
        if not exercise:
            raise NotFoundError("التمرين غير موجود")
        session = await self.session(uid, scenario_id)
        history = session.get("history", [])
        commands_used = [h["command"] for h in history]
        required = exercise.get("required_commands", [])
        missing = [pattern for pattern in required if not any(re.search(pattern, c) for c in commands_used)]
        results = []
        for item in payload.answers:
            question = next((q for q in exercise.get("questions", []) if q["id"] == item.question_id), None)
            if not question:
                raise ValidationError("سؤال لا ينتمي للتمرين")
            results.append(score_question(question, item.answer))
        answered = {r["question_id"] for r in results}
        required_q = {q["id"] for q in exercise.get("questions", [])}
        if required_q and not required_q <= answered:
            raise ValidationError("أجب عن أسئلة التمرين كلها")
        earned = sum(r["earned"] for r in results)
        total = sum(r["points"] for r in results) or 1
        answers_pct = 100 * earned / total
        commands_ok = not missing
        passed = commands_ok and answers_pct >= exercise.get("passing_score", 70)
        record = {"exercise_id": exercise["id"], "passed": passed, "answers_percentage": round(answers_pct, 2),
                  "commands_ok": commands_ok, "missing_commands": missing, "results": results,
                  "validated_at": utc_now()}
        if passed:
            completed = list(dict.fromkeys(session.get("completed_exercises", []) + [exercise["id"]]))
            await self.repo.update(f"lab_sessions/{safe_key(uid)}/{safe_key(scenario_id)}",
                                   {"completed_exercises": completed})
            await self.activity.record(uid, "lab_exercise", exercise["title"], scenario_id, round(answers_pct, 2))
            from app.service_achievements import AchievementService
            await AchievementService(self.repo).evaluate(uid)
        return record
