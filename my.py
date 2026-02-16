import random

money = 100000;

def getDimePoint():
    return random.randint(1, 6) + random.randint(1, 6)

max_money = money;
while money > 0:
    print(f"Your current balance is: ${money}")
    bet = random.randint(1, money // 2) if money > 10 else money
    # print(f"You have placed a bet of: ${bet}")

    max_money = max(money, max_money);
    roll = getDimePoint();
    if roll == 7 or roll == 11:
        # print(f"You rolled a {roll}. You win!")
        money += bet
    elif roll == 2 or roll == 3 or roll == 12:
        # print(f"You rolled a {roll}. You lose!")
        money -= bet
    else:
        prev_Roll = roll
        # print(f"You rolled a {roll}. It's a draw!")
        while True:
            roll = getDimePoint();
            if roll == prev_Roll:
                # print("You win!")
                money += bet
                break
            elif roll == 7:
                money -= bet
                break

print("Game over! You are out of money.")
print(f"You reached a maximum of: ${max_money}")

