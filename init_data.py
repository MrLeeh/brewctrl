#!-*- coding: utf-8 -*-
"""
:author: Stefan Lehmann <stefan.st.lehmann@gmail.com>

"""
from app import create_app, db
from app.models import Step


app = create_app('default')

with app.app_context():
    # delete old step templates
    for step in Step.query.filter(Step.template):
        db.session.delete(step)
    db.session.commit()

    # add step templates
    step_templates = [
        Step(
            name='Vorlösen',
            setpoint=20,
            duration=20,
            comment='Diese Raststufe folgt unmittelbar auf das Einmaischen und ermöglicht es den Malzenzymen besonders gut in Lösung zu gehen. Allerdings sind heutige Malze so hochwertig vorverarbeitet, daß dieser Schritt normalerweise nicht mehr notwendig ist.'
        ),
        Step(
            name='Gummirast',
            setpoint=39,
            duration=15,
            comment='Vor allem Roggen enthält einen hohen Anteil an Glukanen, die ein Bestandteil der Zellwand sind. Sie machen die Würze zähflüssig ("gummiartig"), sodaß ein mit Roggen gebrautes Bier beim Läutervorgang und, je nach Anteil, in der Gärung und sogar beim Trinken unerwünscht klebrig sein kann. Der Abbau durch eine Glukanaserast empfiehlt sich speziell bei Roggenbier.'
        ),
        Step(
            name='Weizenrast1',
            setpoint=45,
            duration=15,
            comment='Besonders Weizenmalz enthält einige Vorläuferstoffe der Ferulasäure, deren Abbauprodukte später zu einigen typischen Weizenbieraromen (wie etwa Nelken) führen. Diese Vorläufer werden zunächst gelöst (Rast 1) und dann zur Ferulasäure abgebaut (Rast 2). Die Rastbereiche liegen eng beieinander.'
        ),
        Step(
            name='Weizenrast2',
            setpoint=48,
            duration=15,
            comment='Besonders Weizenmalz enthält einige Vorläuferstoffe der Ferulasäure, deren Abbauprodukte später zu einigen typischen Weizenbieraromen (wie etwa Nelken) führen. Diese Vorläufer werden zunächst gelöst (Rast 1) und dann zur Ferulasäure abgebaut (Rast 2). Die Rastbereiche liegen eng beieinander.'
        ),
        Step(
            name='Eiweißrast',
            setpoint=52,
            duration=10,
            comment='Jedes Braugetreide enthält Proteine in irgendeiner Form. Einige davon sind erwünscht, etwa Aminosäuren, die der Gärung zugutekommen oder jene Moleküle, die für eine appetitliche Schaumbildung auf dem fertigen Bier sorgen. Andere sind hingegen unerwünscht, da sie zu Kältetrübungen führen Die meisten heute angebotenen Gerstenmalze sind auch hinsichtlich der Proteine bereits durch das Mälzen gut vorgelöst, sodaß heute oft empfohlen wird, keine Eiweißrast mehr durchzuführen. Da hierzu unterschiedliche Meinungen bestehen und das sicher auch von Malz zu Malz, ja von Charge zu Charge verschieden sein kann, ist diese Entscheidung immer versuchsabhängig. Pauschal läßt sich sagen, daß Weizenmalze generell deutlich mehr (auch ungelöste) Eiweiße enthalten und eine Eiweißrast hier deshalb eher empfehlenswert ist.'
        ),
        Step(
            name='Maltoserast',
            setpoint=63,
            duration=45,
            comment='Diese mit der nachfolgenden zusammen wichtigste Rast läßt die Stärke des Malzes von den Beta-Amylasen zu vergärbaren Zuckern (Maltose) abbauen und bestimmt damit den späteren Alkoholgehalt des Bieres. Ein konstantes Rühren ist für eine gute Enzymarbeit in dieser Rast unentbehrlich, sodaß viele Hobbybrauer sich hier eines Rührwerks oder eines extra abgestellten Brauhelfers bedienen (im Rahmen der familiären Freizeitgestaltung auch hervorragend für Kinder geeignet). War die Maische bis zu dieser Rast eher milchig-trüb, läßt sich jetzt der fortschreitende Stärkeabbau verfolgen. Mit fortschreitender Rastdauer wird die Maische klarer und durch den sich zunehmend lösenden Malzzucker auch süßer und klebriger.'
        ),
        Step(
            name='Verzuckerungsrast',
            setpoint=72,
            duration=30,
            comment='Der Name läßt es ahnen: Hier entstehen in großer Menge aus den langen Stärkemolekülen kürzere Zuckermoleküle. Überwiegend sind das in dieser Rast nicht vergärbare Zucker, die dem späteren Bier Vollmundigkeit und Geschmack geben. Neben der Maltoserast die wichtigste; ein Bier, das ausschließlich aus vergärbaren Zuckern hergestellt würde, ginge ordentlich ins Blut – schmeckte aber nach nichts. (Es soll Flüssigkeiten geben, die diesem Szenario recht nahe kommen.) Spätestens nach dieser Rast muß der Stärkenachweis durch eine Jodprobe negativ, also jodnormal ausfallen. Sobald dies der Fall ist, kann die Verzuckerung beendet werden.'
        ),
        Step(
            name='Abmaischen',
            setpoint=78,
            duration=20,
            comment='Wie schon erwähnt, stehen die beiden wärmsten Raststufen in einer Wechselwirkung; was in der heißeren an unvergärbaren Zuckern entsteht, können die Enzyme der kühleren Stufe nachträglich weiter zu vergärbaren Zuckern abbauen. Nicht immer ist dies aber erwünscht. Um ein möglichst vollmundiges Bier mit geringem Alkoholgehalt zu erhalten, muß also die Tätigkeit der Beta-Amylasen nachhaltig beendet werden. Dies geschieht durch Hitze, die übrigens auch dafür sorgt, daß der nachfolgende Läutervorgang durch geringere Viskosität besser abläuft und sich enststandene Zucker mit dem Nachgußwasser besser auswaschen lassen. Wichtig ist, die Maische auf nicht mehr als 80 °C zu erhitzen, da sich oberhalb dieser Grenze unverzuckerte Stärke und unerwünschte Stoffe aus den Spelzen lösen können, die den Gärverlauf und den späteren Geschmack beeinträchtigen.'
        )
    ]

    for step in step_templates:
        step.template = True
        db.session.add(step)

    db.session.commit()
